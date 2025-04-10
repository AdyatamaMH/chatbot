import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv

load_dotenv("credentials.env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            use_pure=True,
            unix_socket=None
        )
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None

@app.get("/get_mysql_data")
def get_mysql_data():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to database.")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT actor_id AS id, first_name AS column1, last_name AS column2, last_update AS column3 FROM actor"
        )
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

class QueryRequest(BaseModel):
    query: str
    selectedRows: list[int]

@app.post("/query_mysql_ai")
def query_mysql_ai(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    response_text = (
        f"You asked: '{request.query}'\n"
        f"You selected {len(request.selectedRows)} row(s): {request.selectedRows}"
    )
    
    return {
        "response": response_text,
        "context": "No AI processing yet — just a test connection."
    }
