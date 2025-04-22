import os
import requests
import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

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
            use_pure=True
        )
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        return None

# ✅ Endpoint: Get list of tables
@app.get("/get_table_list")
def get_table_list():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to database.")
    
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    finally:
        cursor.close()
        conn.close()

# ✅ Endpoint: Get data from specific table
@app.get("/get_mysql_data/{table_name}")
def get_mysql_data(table_name: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to database.")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 100")
        results = cursor.fetchall()

        # Ensure each row has an "id" field for frontend selection
        if results and "id" not in results[0]:
            for i, row in enumerate(results):
                row["id"] = i  # fallback id
        return results
    finally:
        cursor.close()
        conn.close()

# ✅ Query Model Schema
class QueryRequest(BaseModel):
    query: str
    selectedRows: List[Dict]

# ✅ Endpoint: Query with context
@app.post("/query_mysql_ai")
def query_mysql_ai(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not request.selectedRows:
        context = "No data was selected."
    else:
        context_lines = [
            f"Row {i+1}: " + ", ".join(f"{k}: {v}" for k, v in row.items())
            for i, row in enumerate(request.selectedRows)
        ]
        context = "\n".join(context_lines)

    prompt = f"""Context:
{context}

Question:
{request.query}
"""

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        ai_response = response.json().get("response", "No response from Mistral.")
    except Exception as e:
        print("Ollama/Mistral error:", e)
        raise HTTPException(status_code=500, detail="AI model error.")

    return {
        "response": ai_response,
        "context": context
    }
