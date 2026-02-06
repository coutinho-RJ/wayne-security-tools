# Wayne Security Tools

Sistema web para cadastro e gerenciamento de recursos das Indústrias Wayne (projeto final do curso).

## Funcionalidades
- Autenticação com perfis (admin/gerente/usuário).
- Gestão de recursos: criar, editar, remover, entradas e baixas.
- Painel com indicadores e logs de ações.
- Sugestão automática de imagem via Unsplash com pré-visualização.
- Atribuição automática do autor/Unsplash conforme diretrizes.

## Tecnologias
- Python + Flask
- MySQL
- HTML, CSS e JavaScript
- Unsplash API

## Requisitos
- Python 3.9+ (recomendado)
- MySQL em execução

## Configuração

### 1) Ambiente virtual (opcional, recomendado)
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2) Instalar dependências
Como `requirements.txt` ainda está vazio, instale manualmente:
```powershell
pip install flask mysql-connector-python requests python-dotenv
```

### 3) Variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com sua chave do Unsplash:
```
UNSPLASH_ACCESS_KEY=SUA_ACCESS_KEY
```

### 4) Banco de dados
Edite `db.py` com suas credenciais do MySQL e garanta que o banco `wayne_security` exista.

O script de criação das tabelas não está neste repositório. Use o seu script do curso ou exporte do MySQL.

## Executando
```powershell
python app.py
```
Abra no navegador:
```
http://127.0.0.1:5000
```

## Criar usuário admin
Existe um script para criar um admin inicial:
```powershell
python create_admin.py
```
Depois altere a senha no banco.

## Observações
- O arquivo `.env` não deve ser versionado (já está no `.gitignore`).
- Para manter conformidade com a Unsplash, o sistema registra o download quando o recurso é salvo.

## Licença
Sem licença definida.
