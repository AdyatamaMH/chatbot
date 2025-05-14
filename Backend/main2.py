import os
import base64
import io
import requests
import mysql.connector
import matplotlib.pyplot as plt
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
    except mysql.connector.Error:
        return None

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

@app.get("/get_mysql_data/{table_name}")
def get_mysql_data(table_name: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to database.")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 100")
        results = cursor.fetchall()
        if results and "id" not in results[0]:
            for i, row in enumerate(results):
                row["id"] = i
        return results
    finally:
        cursor.close()
        conn.close()

class QueryRequest(BaseModel):
    query: str
    selectedRows: List[Dict]

def is_numeric(value):
    try:
        float(value)
        return True
    except:
        return False

def generate_sample_chart_data(rows: List[Dict]) -> Dict:
    if not rows:
        return None
    sample = rows[0]
    numeric_columns = [k for k, v in sample.items() if is_numeric(v)]
    categorical_columns = [k for k in sample if k not in numeric_columns]
    if not numeric_columns:
        return None
    y_col = numeric_columns[0]
    x_col = categorical_columns[0] if categorical_columns else "index"
    labels = [str(row.get(x_col, f"Row {i+1}")) for i, row in enumerate(rows)]
    values = [float(row[y_col]) for row in rows]
    return {
        "labels": labels,
        "datasets": [
            {
                "label": y_col,
                "data": values,
                "backgroundColor": "rgba(75, 192, 192, 0.6)"
            }
        ]
    }

def generate_base64_image(rows: List[Dict]) -> str:
    if not rows:
        return None
    sample = rows[0]
    numeric_columns = [k for k, v in sample.items() if is_numeric(v)]
    categorical_columns = [k for k in sample if k not in numeric_columns]
    if not numeric_columns:
        return None
    y_col = numeric_columns[0]
    x_col = categorical_columns[0] if categorical_columns else "index"
    labels = [str(row.get(x_col, f"Row {i+1}")) for i, row in enumerate(rows)]
    values = [float(row[y_col]) for row in rows]

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="skyblue")
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"{y_col} by {x_col}")
    plt.xticks(rotation=45)

    min_val = min(values)
    max_val = max(values)
    margin = (max_val - min_val) * 0.05 or 1
    plt.ylim(min_val - margin, max_val + margin)
    tick_interval = max((max_val - min_val) / 5, 1)
    ticks = [round(min_val + i * tick_interval, 2) for i in range(6)]
    plt.yticks(ticks)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

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

    def clean_query_for_ai(query: str) -> str:
        replacements = {
            "chart": "summary",
            "graph": "summary",
            "plot": "summary",
            "visualize": "analyze",
            "visualization": "summary"
        }
        for word, replacement in replacements.items():
            query = query.replace(word, replacement)
        return query

    cleaned_query = clean_query_for_ai(request.query.lower())

    prompt = f"""Context:
{context}

Question:
{cleaned_query}
"""

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        ai_response = response.json().get("response", "No response from Mistral.")
    except Exception:
        raise HTTPException(status_code=500, detail="AI model error.")

    query_lower = request.query.lower()
    chart_data = generate_sample_chart_data(request.selectedRows) if "chart" in query_lower else None
    image_base64 = generate_base64_image(request.selectedRows) if "graph" in query_lower else None

    return {
        "response": ai_response,
        "chartData": chart_data,
        "imageBase64": image_base64,
    }
