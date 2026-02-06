# db.py
import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",          # ajuste conforme seu ambiente
        password="Fla-2019", # ajuste conforme seu ambiente
        database="wayne_security"
    )
    return conn
