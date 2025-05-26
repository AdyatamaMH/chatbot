import os
import json
import base64
import io
import re
import numpy as np
import pandas as pd
import faiss
import ollama
import requests
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from typing import List, Dict, Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_FOLDER = "data"
INDEX_FOLDER = "index_store"
INDEX_PATH = os.path.join(INDEX_FOLDER, "csv_index.faiss")
METADATA_PATH = os.path.join(INDEX_FOLDER, "csv_metadata.json")
os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(INDEX_FOLDER, exist_ok=True)

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384
index = faiss.IndexFlatL2(dimension)
if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
else:
    metadata = []

def row_to_text(row):
    return ", ".join([f"{col}: {row[col]}" for col in row.index])

@app.post("/upload_csv")
def upload_csv(file: UploadFile = File(...)):
    file_location = os.path.join(CSV_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    df = pd.read_csv(file_location)
    docs = df.apply(row_to_text, axis=1).tolist()
    new_embeddings = normalize(embed_model.encode(docs), norm='l2', axis=1)
    global index, metadata
    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r") as f:
            existing_metadata = json.load(f)
        index.add(np.array(new_embeddings))
        existing_metadata.extend(df.to_dict(orient="records"))
        metadata = existing_metadata
    else:
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(new_embeddings))
        metadata = df.to_dict(orient="records")
    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f)
    return {"message": "CSV uploaded and indexed successfully"}

def extract_query_attributes(query, records):
    attrs = {}
    for record in records:
        for key in record:
            match = re.search(rf"{key}\s*:\s*(.+?)(?=\s*\w+[:]|$)", query, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
                    attrs[key] = datetime.strptime(val, "%Y-%m-%d")
                elif re.match(r"^\d+(\.\d+)?$", val):
                    attrs[key] = float(val) if "." in val else int(val)
                else:
                    attrs[key] = val
    return attrs

def retrieve_context(query):
    if not metadata:
        return None
    q_emb = normalize(embed_model.encode([query]), norm='l2', axis=1)
    dists, ids = index.search(np.array(q_emb), len(metadata))
    rows = [metadata[i] for i in ids[0] if i < len(metadata)]
    attrs = extract_query_attributes(query, rows)
    for k,v in attrs.items():
        rows = [r for r in rows if (isinstance(v, datetime) and datetime.strptime(r.get(k,""), "%Y-%m-%d")==v) or r.get(k)==v]
    return rows[0] if rows else None

def format_context(ctx):
    if not ctx:
        return "No relevant data found."
    return (f"On {ctx.get('business_date','?')}, at {ctx.get('business_unit','?')}, "
            f"balance tier {ctx.get('balance_tier_description','?')}, "
            f"total balance {ctx.get('total_balance',0):,.2f} IDR, "
            f"{ctx.get('no_of_customers',0)} customers.")

def format_text(txt):
    return re.sub(r"(\d+\.)\s*", r"\n\1 ", txt).strip()

class CSVQuery(BaseModel):
    query: str

@app.post("/query")
def query_csv(request: CSVQuery):
    ctx = retrieve_context(request.query)
    fmt = format_context(ctx)
    input_text = f"Context: {fmt}\nQuestion: {request.query}"
    try:
        res = ollama.chat(model="mistral", messages=[{"role":"user","content":input_text}])
        return {"response": format_text(res["message"]["content"]), "context": fmt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

DB_CONFIG = {"host": "", "user": "", "password": "", "database": ""}

class MySQLCredentials(BaseModel):
    host: str
    user: str
    password: Optional[str] = ""
    database: str

@app.post("/update_mysql_credentials")
def update_mysql_credentials(creds: MySQLCredentials):
    global DB_CONFIG
    DB_CONFIG = creds.dict()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Connection failed: {err}")
    return {"message": "MySQL credentials updated"}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG, use_pure=True)
    except mysql.connector.Error:
        return None

@app.get("/get_table_list")
def get_table_list():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(500, "DB connect error")
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return tables

@app.get("/get_mysql_data/{table}")
def get_mysql_data(table: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(500, "DB connect error")
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT * FROM `{table}` LIMIT 100")
    rows = cur.fetchall()
    cur.close(); conn.close()
    if rows and "id" not in rows[0]:
        for i,row in enumerate(rows):
            row["id"] = i
    return rows

class MySQLQuery(BaseModel):
    query: str
    selectedRows: List[Dict]

def is_numeric(v):
    try: float(v); return True
    except: return False

COLUMN_SYNONYMS = {
    "sales": "store_sales",
    "income": "store_sales",
    "revenue": "store_sales",
    "customers": "no_of_customers",
    "length": "length",
    "balance": "total_balance",
    "quantity": "quantity",
    "amount": "total_balance",
    "id": "id"
}

def gen_chart_data(rows: List[Dict], user_query: str = "") -> Dict:
    if not rows:
        return None
    sample = rows[0]
    numeric_columns = [k for k, v in sample.items() if is_numeric(v)]
    categorical_columns = [k for k in sample if k not in numeric_columns]
    if not numeric_columns:
        return None
    user_query_lower = user_query.lower()
    preferred_col = None
    for word in user_query_lower.split():
        if word in COLUMN_SYNONYMS:
            candidate = COLUMN_SYNONYMS[word]
            if candidate in numeric_columns:
                preferred_col = candidate
                break
    if not preferred_col:
        for col in numeric_columns:
            if col.lower() in user_query_lower:
                preferred_col = col
                break
    if not preferred_col:
        preferred_col = numeric_columns[0]
    x_col = categorical_columns[0] if categorical_columns else "index"
    labels = [str(row.get(x_col, f"Row {i+1}")) for i, row in enumerate(rows)]
    values = [float(row[preferred_col]) for row in rows if is_numeric(row[preferred_col])]
    return {
        "labels": labels,
        "datasets": [
            {
                "label": preferred_col,
                "data": values,
                "backgroundColor": "rgba(75, 192, 192, 0.6)"
            }
        ]
    }

def gen_image(rows: List[Dict], user_query: str = "") -> str:
    chart_data = gen_chart_data(rows, user_query)
    if not chart_data:
        return None
    labels = chart_data["labels"]
    values = chart_data["datasets"][0]["data"]
    y_label = chart_data["datasets"][0]["label"]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="skyblue")
    plt.xlabel("Category")
    plt.ylabel(y_label)
    plt.title(f"{y_label} by Category")
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
def query_mysql_ai(req: MySQLQuery):
    if not req.query:
        raise HTTPException(400, "Empty query")

    ctx = "\n".join(
        f"Row {i+1}: " + ", ".join(f"{k}: {v}" for k, v in row.items())
        for i, row in enumerate(req.selectedRows)
    ) or "No data selected."

    cleaned = re.sub(r"\b(chart|graph|plot|visualization)\b", "summary", req.query, flags=re.IGNORECASE)
    prompt = f"Context:\n{ctx}\n\nQuestion:\n{cleaned}"

    try:
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })
        r.raise_for_status()
        ai_resp = r.json().get("response", "")
    except:
        raise HTTPException(500, "AI error")

    user_query_lower = req.query.lower()
    return_chart = "chart" in user_query_lower
    return_graph = "graph" in user_query_lower

    return {
        "response": ai_resp,
        "chartData": gen_chart_data(req.selectedRows, req.query) if return_chart else None,
        "imageBase64": gen_image(req.selectedRows, req.query) if return_graph else None
    }