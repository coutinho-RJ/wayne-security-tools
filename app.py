from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import get_connection
import os
import requests
from dotenv import load_dotenv
from collections import OrderedDict
import time

app = Flask(__name__)
app.secret_key = "batcaverna_super_secreta"  # troque em produção

# ===== Carregar vari?veis de ambiente (.env) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path, override=True)

def _clean_key(value):
    if not value:
        return ""
    key = value.strip()
    # Remove BOM se existir
    key = key.replace("\ufeff", "")
    # Remove aspas no inicio/fim
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    return key

UNSPLASH_ACCESS_KEY = _clean_key(os.getenv("UNSPLASH_ACCESS_KEY"))
UNSPLASH_APP_NAME = "industrias_wayne_security_tools"
UNSPLASH_UTM_PARAMS = f"utm_source={UNSPLASH_APP_NAME}&utm_medium=referral&utm_campaign=api-credit"

def _add_utm(url):
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{UNSPLASH_UTM_PARAMS}"
# ================================================

UNSPLASH_CACHE_TTL = 600
UNSPLASH_CACHE_MAX = 200
_unsplash_cache = OrderedDict()

def _normalize_query(q):
    return " ".join(q.lower().split())

def _cache_get(key):
    item = _unsplash_cache.get(key)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > UNSPLASH_CACHE_TTL:
        _unsplash_cache.pop(key, None)
        return None
    _unsplash_cache.move_to_end(key)
    return data

def _cache_set(key, data):
    _unsplash_cache[key] = (time.time(), data)
    _unsplash_cache.move_to_end(key)
    if len(_unsplash_cache) > UNSPLASH_CACHE_MAX:
        _unsplash_cache.popitem(last=False)

# --- Filtro para formatar moeda em padrão brasileiro ---
@app.template_filter("brl")
def format_brl(value):
    """
    Formata números como moeda brasileira: R$ 1.234,56
    """
    try:
        valor = float(value)
    except (TypeError, ValueError):
        return value

    # 1.234,56
    s = f"{valor:,.2f}"
    # troca pontos por vírgulas e vírgulas por pontos
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


@app.context_processor
def inject_pendencias():
    pendentes_baixas = 0

    if "user_role" in session and session["user_role"] in ["gerente", "admin"]:
        conn = get_connection()
        cursor = conn.cursor()

        if session["user_role"] == "gerente":
            # gerente vê apenas pendentes
            cursor.execute("SELECT COUNT(*) FROM resource_requests WHERE status = 'pendente'")
        else:
            # admin vê pendentes e aprovados pelo gerente
            cursor.execute("""
                SELECT COUNT(*) FROM resource_requests
                WHERE status IN ('pendente', 'aprovado_gerente')
            """)

        pendentes_baixas = cursor.fetchone()[0]
        cursor.close()
        conn.close()

    return dict(pendentes_baixas=pendentes_baixas)


# =========================
# DECORADORES E LOG
# =========================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_role" not in session:
                return redirect(url_for("login"))
            if session["user_role"] not in roles:
                flash("Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated
    return wrapper


def log_action(user_id, action, details=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO access_logs (user_id, action, details) VALUES (%s, %s, %s)",
        (user_id, action, details)
    )
    conn.commit()
    cursor.close()
    conn.close()

# =========================
# ROTAS BÁSICAS
# =========================

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.name, u.username, u.password_hash, u.approved,
                   r.name AS role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = %s
        """, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not user["approved"]:
            flash("Usuário não autorizado ou aguardando aprovação.", "danger")
        elif user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role_name"]
            log_action(user["id"], "login", "Login realizado com sucesso")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    user_id = session.get("user_id")
    log_action(user_id, "logout", "Logout do sistema")
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Quantidade total de recursos
    cursor.execute("SELECT COUNT(*) AS total FROM resources")
    total_recursos = cursor.fetchone()["total"]

    # Quantidade por status
    cursor.execute("""
        SELECT status, COUNT(*) AS total
        FROM resources
        GROUP BY status
    """)
    recursos_por_status = cursor.fetchall()

    # Últimos logs
    cursor.execute("""
        SELECT al.action, al.details, al.created_at, u.name AS user_name
        FROM access_logs al
        JOIN users u ON u.id = al.user_id
        ORDER BY al.created_at DESC
        LIMIT 10
    """)
    ultimos_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_recursos=total_recursos,
        recursos_por_status=recursos_por_status,
        ultimos_logs=ultimos_logs
    )

# =========================
# GESTÃO DE RECURSOS
# =========================

@app.route("/recursos")
@login_required
def recursos_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id,
               r.name,
               r.description,
               r.status,
               r.location,
               r.price,
               r.quantity,
               r.image_url,
               rt.name AS type_name
        FROM resources r
        JOIN resource_types rt ON r.type_id = rt.id
        ORDER BY r.created_at DESC
    """)
    recursos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("recursos_list.html", recursos=recursos)


@app.route("/recursos/novo", methods=["GET", "POST"])
@login_required
@role_required("gerente", "admin")
def recurso_novo():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM resource_types")
    tipos = cursor.fetchall()

    if request.method == "POST":
        name        = request.form.get("name")
        description = request.form.get("description")
        type_id     = request.form.get("type_id")
        location    = request.form.get("location")
        status      = request.form.get("status")
        price       = request.form.get("price") or 0
        quantity    = request.form.get("quantity") or 0
        image_url   = request.form.get("image_url") or None

        cursor.execute("""
            INSERT INTO resources (name, description, type_id, location, status, price, quantity, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, description, type_id, location, status, price, quantity, image_url))
        conn.commit()

        log_action(session["user_id"], "criou recurso", f"Recurso: {name}")

        cursor.close()
        conn.close()
        flash("Recurso criado com sucesso!", "success")
        return redirect(url_for("recursos_list"))

    cursor.close()
    conn.close()
    return render_template("recursos_form.html", tipos=tipos, recurso=None)


@app.route("/recursos/editar/<int:recurso_id>", methods=["GET", "POST"])
@login_required
@role_required("gerente", "admin")
def recurso_editar(recurso_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM resource_types")
    tipos = cursor.fetchall()

    cursor.execute("SELECT * FROM resources WHERE id = %s", (recurso_id,))
    recurso = cursor.fetchone()

    if not recurso:
        cursor.close()
        conn.close()
        flash("Recurso não encontrado.", "danger")
        return redirect(url_for("recursos_list"))

    if request.method == "POST":
        name        = request.form.get("name")
        description = request.form.get("description")
        type_id     = request.form.get("type_id")
        location    = request.form.get("location")
        status      = request.form.get("status")
        price       = request.form.get("price") or 0
        quantity    = request.form.get("quantity") or 0
        image_url   = request.form.get("image_url") or None

        cursor.execute("""
            UPDATE resources
            SET name = %s,
                description = %s,
                type_id = %s,
                location = %s,
                status = %s,
                price = %s,
                quantity = %s,
                image_url = %s
            WHERE id = %s
        """, (name, description, type_id, location, status, price, quantity, image_url, recurso_id))
        conn.commit()

        log_action(session["user_id"], "editou recurso", f"Recurso: {name} (ID {recurso_id})")

        cursor.close()
        conn.close()
        flash("Recurso atualizado com sucesso!", "success")
        return redirect(url_for("recursos_list"))

    cursor.close()
    conn.close()
    return render_template("recursos_form.html", tipos=tipos, recurso=recurso)


@app.route("/recursos/remover/<int:recurso_id>", methods=["POST"])
@login_required
@role_required("admin")
def recurso_remover(recurso_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM resources WHERE id = %s", (recurso_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        flash("Recurso não encontrado.", "danger")
        return redirect(url_for("recursos_list"))

    name = row[0]

    cursor.execute("DELETE FROM resources WHERE id = %s", (recurso_id,))
    conn.commit()

    log_action(session["user_id"], "removeu recurso", f"Recurso: {name} (ID {recurso_id})")

    cursor.close()
    conn.close()
    flash("Recurso removido com sucesso!", "success")
    return redirect(url_for("recursos_list"))

# =========================
# SOLICITAÇÕES DE BAIXA DE ESTOQUE
# =========================

@app.route("/recursos/<int:recurso_id>/baixa", methods=["GET", "POST"])
@login_required
@role_required("funcionario", "gerente", "admin")
def recurso_baixa_solicitar(recurso_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, price, quantity
        FROM resources
        WHERE id = %s
    """, (recurso_id,))
    recurso = cursor.fetchone()

    if not recurso:
        cursor.close()
        conn.close()
        flash("Recurso não encontrado.", "danger")
        return redirect(url_for("recursos_list"))

    if request.method == "POST":
        try:
            qty = int(request.form.get("quantity") or 0)
        except ValueError:
            qty = 0

        if qty <= 0:
            flash("Quantidade inválida.", "danger")
            cursor.close()
            conn.close()
            return render_template("baixa_form.html", recurso=recurso)

        if qty > recurso["quantity"]:
            flash("Quantidade solicitada maior que o estoque disponível.", "danger")
            cursor.close()
            conn.close()
            return render_template("baixa_form.html", recurso=recurso)

        total_value = recurso["price"] * qty

        try:
            # 1) cria solicitação
            cursor.execute("""
                INSERT INTO resource_requests (resource_id, requested_by, quantity, total_value, status)
                VALUES (%s, %s, %s, %s, 'pendente')
            """, (recurso_id, session["user_id"], qty, total_value))

            # 2) já retira do estoque (reserva)
            cursor.execute("""
                UPDATE resources
                SET quantity = quantity - %s
                WHERE id = %s
            """, (qty, recurso_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            flash(f"Erro ao criar solicitação de baixa: {e}", "danger")
            return render_template("baixa_form.html", recurso=recurso)

        log_action(
            session["user_id"],
            "solicitou baixa",
            f"Recurso ID {recurso_id}, qtd {qty}, valor total {total_value}"
        )

        cursor.close()
        conn.close()
        flash("Solicitação de baixa criada e estoque reservado. Aguardando aprovação.", "success")
        return redirect(url_for("recursos_list"))

    cursor.close()
    conn.close()
    return render_template("baixa_form.html", recurso=recurso)


@app.route("/recursos/<int:recurso_id>/entrada", methods=["GET", "POST"])
@login_required
@role_required("funcionario", "gerente", "admin")
def recurso_entrada(recurso_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, price, quantity
        FROM resources
        WHERE id = %s
    """, (recurso_id,))
    recurso = cursor.fetchone()

    if not recurso:
        cursor.close()
        conn.close()
        flash("Recurso não encontrado.", "danger")
        return redirect(url_for("recursos_list"))

    if request.method == "POST":
        try:
            qty = int(request.form.get("quantity") or 0)
        except ValueError:
            qty = 0

        if qty <= 0:
            flash("Quantidade inválida.", "danger")
            cursor.close()
            conn.close()
            return render_template("entrada_form.html", recurso=recurso)

        novo_estoque = recurso["quantity"] + qty

        cursor.execute("""
            UPDATE resources
            SET quantity = %s
            WHERE id = %s
        """, (novo_estoque, recurso_id))
        conn.commit()

        log_action(
            session["user_id"],
            "entrada estoque",
            f"Recurso ID {recurso_id}, qtd adicionada {qty}, novo estoque {novo_estoque}"
        )

        cursor.close()
        conn.close()
        flash("Entrada de estoque registrada com sucesso!", "success")
        return redirect(url_for("recursos_list"))

    cursor.close()
    conn.close()
    return render_template("entrada_form.html", recurso=recurso)



@app.route("/baixas")
@login_required
@role_required("gerente", "admin")
def baixas_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT rr.id, rr.resource_id, rr.quantity, rr.total_value, rr.status,
               rr.created_at, rr.manager_id, rr.admin_id,
               r.name AS resource_name,
               u.name AS requester_name
        FROM resource_requests rr
        JOIN resources r ON r.id = rr.resource_id
        JOIN users u ON u.id = rr.requested_by
        ORDER BY rr.created_at DESC
    """)
    requests = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("baixas_list.html", requests=requests)


def _executar_baixa(conn, cursor, request_row, approver_role, approver_id):
    """
    Conclui a aprovação da baixa.
    O estoque já foi reservado na criação da solicitação,
    então aqui só atualizamos o status e quem aprovou.
    """
    if approver_role == "gerente":
        cursor.execute("""
            UPDATE resource_requests
            SET status = 'aprovado', manager_id = %s
            WHERE id = %s
        """, (approver_id, request_row["id"]))
    else:  # admin
        cursor.execute("""
            UPDATE resource_requests
            SET status = 'aprovado', admin_id = %s
            WHERE id = %s
        """, (approver_id, request_row["id"]))


@app.route("/baixas/<int:request_id>/aprovar", methods=["POST"])
@login_required
@role_required("gerente", "admin")
def baixa_aprovar(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM resource_requests
        WHERE id = %s
    """, (request_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        conn.close()
        flash("Solicitação não encontrada.", "danger")
        return redirect(url_for("baixas_list"))

    role = session["user_role"]
    total_value = req["total_value"]

    try:
        if role == "gerente":
            if req["status"] != "pendente":
                raise ValueError("Solicitação já processada.")
            if total_value > 10000:
                # aprova parcialmente, aguardando admin
                cursor.execute("""
                    UPDATE resource_requests
                    SET status = 'aprovado_gerente', manager_id = %s
                    WHERE id = %s
                """, (session["user_id"], request_id))
            else:
                # gerente pode concluir a baixa
                _executar_baixa(conn, cursor, req, "gerente", session["user_id"])
        else:  # admin
            if total_value > 10000:
                if req["status"] != "aprovado_gerente":
                    raise ValueError("Solicitação acima de 10.000 precisa da aprovação prévia do gerente.")
                _executar_baixa(conn, cursor, req, "admin", session["user_id"])
            else:
                # admin pode aprovar sozinho também
                _executar_baixa(conn, cursor, req, "admin", session["user_id"])

        conn.commit()
        log_action(session["user_id"], "aprovou baixa", f"Solicitação ID {request_id}, valor {total_value}")
        flash("Baixa aprovada com sucesso.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Erro ao aprovar baixa: {e}", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("baixas_list"))


@app.route("/baixas/<int:request_id>/rejeitar", methods=["POST"])
@login_required
@role_required("gerente", "admin")
def baixa_rejeitar(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, resource_id, quantity, status
        FROM resource_requests
        WHERE id = %s
    """, (request_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        conn.close()
        flash("Solicitação não encontrada.", "danger")
        return redirect(url_for("baixas_list"))

    if req["status"] == "rejeitado":
        cursor.close()
        conn.close()
        flash("Solicitação já foi rejeitada.", "warning")
        return redirect(url_for("baixas_list"))

    try:
        # devolve a quantidade para o estoque
        cursor.execute("""
            UPDATE resources
            SET quantity = quantity + %s
            WHERE id = %s
        """, (req["quantity"], req["resource_id"]))

        cursor.execute("""
            UPDATE resource_requests
            SET status = 'rejeitado'
            WHERE id = %s
        """, (request_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        flash(f"Erro ao rejeitar solicitação: {e}", "danger")
        return redirect(url_for("baixas_list"))

    log_action(session["user_id"], "rejeitou baixa", f"Solicitação ID {request_id}")
    cursor.close()
    conn.close()
    flash("Solicitação rejeitada e estoque devolvido.", "success")
    return redirect(url_for("baixas_list"))


# =========================
# GESTÃO DE USUÁRIOS
# =========================

@app.route("/usuarios")
@login_required
@role_required("gerente", "admin")
def usuarios_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.id, u.name, u.username, u.approved, r.name AS role_name, u.created_at
        FROM users u
        JOIN roles r ON r.id = u.role_id
        ORDER BY u.created_at DESC
    """)
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("usuarios_list.html", usuarios=usuarios)


@app.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@role_required("gerente", "admin")
def usuario_novo():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM roles ORDER BY name")
    roles = cursor.fetchall()

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        role_id = request.form.get("role_id")

        if not name or not username or not password or not role_id:
            flash("Preencha todos os campos.", "danger")
            cursor.close()
            conn.close()
            return render_template("usuario_form.html", roles=roles, usuario=None)

        password_hash = generate_password_hash(password)

        # Se foi o gerente criando, marca como não aprovado ainda
        approved = 0 if session["user_role"] == "gerente" else 1

        try:
            cursor.execute("""
                INSERT INTO users (name, username, password_hash, role_id, approved)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, username, password_hash, role_id, approved))
            conn.commit()

            if approved:
                msg = "Usuário criado e aprovado."
            else:
                msg = "Usuário criado, aguardando aprovação do Admin."

            log_action(session["user_id"], "criou usuario", f"Usuário: {username}")
            flash(msg, "success")
            cursor.close()
            conn.close()
            return redirect(url_for("usuarios_list"))
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            flash(f"Erro ao criar usuário: {e}", "danger")
            return render_template("usuario_form.html", roles=roles, usuario=None)

    cursor.close()
    conn.close()
    return render_template("usuario_form.html", roles=roles, usuario=None)


@app.route("/usuarios/aprovar/<int:usuario_id>", methods=["POST"])
@login_required
@role_required("admin")
def usuario_aprovar(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE id = %s", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("usuarios_list"))

    username = row[1]

    cursor.execute("""
        UPDATE users
        SET approved = 1
        WHERE id = %s
    """, (usuario_id,))
    conn.commit()

    log_action(session["user_id"], "aprovou usuario", f"Usuário: {username} (ID {usuario_id})")

    cursor.close()
    conn.close()
    flash("Usuário aprovado com sucesso.", "success")
    return redirect(url_for("usuarios_list"))


@app.route("/usuarios/editar/<int:usuario_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def usuario_editar(usuario_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM roles ORDER BY name")
    roles = cursor.fetchall()

    cursor.execute("""
        SELECT id, name, username, role_id, approved
        FROM users
        WHERE id = %s
    """, (usuario_id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("usuarios_list"))

    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        role_id = request.form.get("role_id")

        if not name or not username or not role_id:
            flash("Nome, usuário e papel são obrigatórios.", "danger")
            cursor.close()
            conn.close()
            return render_template("usuario_form.html", roles=roles, usuario=usuario)

        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE users
                SET name = %s, username = %s, password_hash = %s, role_id = %s
                WHERE id = %s
            """, (name, username, password_hash, role_id, usuario_id))
        else:
            cursor.execute("""
                UPDATE users
                SET name = %s, username = %s, role_id = %s
                WHERE id = %s
            """, (name, username, role_id, usuario_id))

        conn.commit()
        log_action(session["user_id"], "editou usuario", f"Usuário: {username} (ID {usuario_id})")
        cursor.close()
        conn.close()

        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("usuarios_list"))

    cursor.close()
    conn.close()
    return render_template("usuario_form.html", roles=roles, usuario=usuario)


@app.route("/usuarios/remover/<int:usuario_id>", methods=["POST"])
@login_required
@role_required("admin")
def usuario_remover(usuario_id):
    if usuario_id == session.get("user_id"):
        flash("Você não pode remover o próprio usuário logado.", "danger")
        return redirect(url_for("usuarios_list"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users WHERE id = %s", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("usuarios_list"))

    username = row[0]

    cursor.execute("DELETE FROM users WHERE id = %s", (usuario_id,))
    conn.commit()

    log_action(session["user_id"], "removeu usuario", f"Usuário: {username} (ID {usuario_id})")

    cursor.close()
    conn.close()
    flash("Usuário removido com sucesso!", "success")
    return redirect(url_for("usuarios_list"))

@app.route("/api/unsplash_suggest")
@login_required
def unsplash_suggest():
    """
    Retorna uma sugest?o de imagem do Unsplash com base no par?metro ?q=...
    """
    if not UNSPLASH_ACCESS_KEY:
        return jsonify({
            "ok": False,
            "error": "UNSPLASH_ACCESS_KEY n?o configurada no servidor."
        }), 503

    query = request.args.get("q", "").strip()

    if not query or len(query) < 3:
        return jsonify({
            "ok": False,
            "error": "Termo de busca muito curto."
        }), 400

    qnorm = _normalize_query(query)
    cached = _cache_get(qnorm)
    if cached:
        return jsonify(cached)

    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            },
            headers={
                "Accept-Version": "v1",
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
                "User-Agent": "wayne-security-tools/1.0",
            },
            timeout=5
        )

        data = resp.json()

        if resp.status_code != 200:
            return jsonify({
                "ok": False,
                "error": "Erro ao buscar no Unsplash.",
                "status_code": resp.status_code,
            }), resp.status_code

        if not data.get("results"):
            return jsonify({
                "ok": False,
                "error": "Nenhuma imagem encontrada para esse termo."
            }), 404

        photo = data["results"][0]

        payload = {
            "ok": True,
            "image_url": photo["urls"]["regular"],
            "author_name": photo["user"]["name"],
            "author_url": _add_utm(photo["user"]["links"]["html"]),
            "photo_url": _add_utm(photo["links"]["html"]),
            "unsplash_url": f"https://unsplash.com/?{UNSPLASH_UTM_PARAMS}",
            "download_location": photo["links"]["download_location"],
        }

        _cache_set(qnorm, payload)
        return jsonify(payload)

    except Exception as e:
        print("Erro ao chamar Unsplash:", e)
        return jsonify({
            "ok": False,
            "error": "Erro ao comunicar com o Unsplash."
        }), 500

@app.route("/api/unsplash_download", methods=["POST"])
@login_required
def unsplash_download():
    if not UNSPLASH_ACCESS_KEY:
        return jsonify({
            "ok": False,
            "error": "UNSPLASH_ACCESS_KEY n?o configurada no servidor."
        }), 503

    data = request.get_json(silent=True) or {}
    download_location = (data.get("download_location") or "").strip()

    if not download_location:
        return jsonify({
            "ok": False,
            "error": "download_location n?o informado."
        }), 400

    if not download_location.startswith("https://api.unsplash.com/"):
        return jsonify({
            "ok": False,
            "error": "download_location inv?lido."
        }), 400

    try:
        resp = requests.get(
            download_location,
            headers={
                "Accept-Version": "v1",
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
                "User-Agent": "wayne-security-tools/1.0",
            },
            timeout=5
        )

        if resp.status_code != 200:
            return jsonify({
                "ok": False,
                "error": "Erro ao registrar download.",
                "status_code": resp.status_code,
            }), resp.status_code

        return jsonify({"ok": True})

    except Exception as e:
        print("Erro ao registrar download:", e)
        return jsonify({
            "ok": False,
            "error": "Erro ao comunicar com o Unsplash."
        }), 500
if __name__ == "__main__":
    app.run(debug=True)
