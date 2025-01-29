import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "127.0.0.1"
DB_PORT = "3307"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "grammar_db"

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
