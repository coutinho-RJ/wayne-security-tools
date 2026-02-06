# create_admin.py
from db import get_connection
from werkzeug.security import generate_password_hash

name = "Bruce Wayne"
username = "bruce"
password = "batman123"   # depois troca

conn = get_connection()
cursor = conn.cursor()

# pega o id do papel admin
cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
role_id = cursor.fetchone()[0]

password_hash = generate_password_hash(password)

cursor.execute("""
    INSERT INTO users (name, username, password_hash, role_id)
    VALUES (%s, %s, %s, %s)
""", (name, username, password_hash, role_id))

conn.commit()
cursor.close()
conn.close()

print("Usuário admin criado com sucesso!")
