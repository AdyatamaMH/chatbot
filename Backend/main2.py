import os
import json
import faiss
import numpy as np
import ollama
import re
import mysql.connector
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_FOLDER = "index_store"
INDEX_PATH = os.path.join(INDEX_FOLDER, "mysql_index.faiss")
METADATA_PATH = os.path.join(INDEX_FOLDER, "mysql_metadata.json")

os.makedirs(INDEX_FOLDER, exist_ok=True)

# Load Embedding Model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Load existing index and metadata
if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
else:
    metadata = []

def get_db_connection():
    """Establish a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        return None

def row_to_text(row):
    """Converts a row into a textual description."""
    return ", ".join([f"{col}: {row[col]}" for col in row.keys()])

@app.get("/index_mysql")
def index_mysql_data():
    """Fetches MySQL data and indexes it in FAISS."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM your_table")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return {"message": "No data found in the database."}

    global index, metadata

    # Convert rows to text descriptions
    documents = [row_to_text(row) for row in rows]

    # Generate embeddings
    embeddings = embed_model.encode(documents)
    embeddings = normalize(embeddings, norm='l2', axis=1)

    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "r") as f:
            existing_metadata = json.load(f)

        index.add(np.array(embeddings))
        existing_metadata.extend(rows)
        metadata = existing_metadata
    else:
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings))
        metadata = rows

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f)

    return {"message": "MySQL data indexed successfully."}

def retrieve_context(query, metadata, index, embed_model, top_k=5):
    """Retrieves relevant MySQL rows based on query embeddings."""
    if not metadata:
        return None

    query_embedding = embed_model.encode([query])
    query_embedding = normalize(query_embedding, norm='l2', axis=1)

    distances, indices = index.search(np.array(query_embedding), min(top_k, len(metadata)))

    retrieved_rows = [metadata[idx] for idx in indices[0] if idx < len(metadata)]
    
    return retrieved_rows[0] if retrieved_rows else None

def format_response(context):
    """Formats retrieved MySQL row into a readable message."""
    if not context:
        return "No relevant data found."
    
    return ", ".join([f"{key}: {value}" for key, value in context.items()])

def format_response_text(response_text):
    """Formats response text for readability."""
    return re.sub(r"(\d+\.)\s*", r"\n\1 ", response_text).strip()

class QueryRequest(BaseModel):
    query: str

@app.post("/query_mysql_ai")
def query_mysql_ai(request: QueryRequest):
    """Handles AI-powered MySQL queries."""
    retrieved_context = retrieve_context(request.query, metadata, index, embed_model)
    formatted_context = format_response(retrieved_context)

    input_text = f"Context: {formatted_context} \n Question: {request.query}"

    try:
        response = ollama.chat(model='mistral', messages=[{"role": "user", "content": input_text}])
        formatted_response = format_response_text(response['message']['content'])

        return {
            "response": formatted_response,
            "context": formatted_context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
