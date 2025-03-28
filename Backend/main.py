import os
import json
import faiss
import numpy as np
import ollama
import re
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
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
    """Dynamically converts a row to a textual description."""
    return ", ".join([f"{col}: {row[col]}" for col in row.index])

@app.post("/upload_csv")
def upload_csv(file: UploadFile = File(...)):
    """Handles CSV uploads, saves them, and merges them into the FAISS index."""
    file_location = os.path.join(CSV_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    df = pd.read_csv(file_location)
    
    documents = df.apply(row_to_text, axis=1).tolist()
    
    new_embeddings = embed_model.encode(documents)
    new_embeddings = normalize(new_embeddings, norm='l2', axis=1)

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
    
    return {"message": "CSV uploaded, indexed, and merged successfully."}

def extract_query_attributes(query, metadata):
    """Dynamically extracts attributes from query based on metadata keys."""
    extracted_attributes = {}
    for record in metadata:
        for key in record.keys():
            pattern = rf"{key}\s*:\s*(.+?)(?=\s*\b\w+[:]|$)"
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                try:
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):  
                        extracted_attributes[key] = datetime.strptime(value, "%Y-%m-%d")
                    elif re.match(r"^\d+(\.\d+)?$", value):  
                        extracted_attributes[key] = float(value) if "." in value else int(value)
                    else:
                        extracted_attributes[key] = value  
                except Exception as e:
                    print(f"Conversion error for {key}: {e}")
    return extracted_attributes

def retrieve_context(query, metadata, index, embed_model, top_k=None):
    """Retrieves relevant rows based on query embeddings and filters them dynamically."""
    
    if not metadata:
        return None

    max_rows = len(metadata)
    top_k = (max_rows + 1) if top_k is None else top_k

    query_embedding = embed_model.encode([query])
    query_embedding = normalize(query_embedding, norm='l2', axis=1)
    
    distances, indices = index.search(np.array(query_embedding), min(top_k, len(metadata)))
    
    retrieved_rows = [metadata[idx] for idx in indices[0] if idx < len(metadata)]
    
    attributes = extract_query_attributes(query, retrieved_rows)
    filtered_rows = retrieved_rows

    for attr, value in attributes.items():
        filtered_rows = [
            row for row in filtered_rows
            if row.get(attr) and (row[attr] == value if not isinstance(value, datetime) else datetime.strptime(row[attr], "%Y-%m-%d") == value)
        ]

    return filtered_rows[0] if filtered_rows else None

def format_response(context):
    """Formats the retrieved context into a more readable message."""
    if not context:
        return "No relevant data found."
    
    return (
        f"On {context.get('business_date', 'Unknown Date')}, at {context.get('business_unit', 'Unknown Unit')}, "
        f"the balance tier is {context.get('balance_tier_description', 'Unknown')}, "
        f"with a total balance of {context.get('total_balance', 0):,.2f} IDR. "
        f"The number of customers in this tier is {context.get('no_of_customers', 0)}."
    )

def format_response_text(response_text):
    """Formats response text for better readability."""
    formatted_text = re.sub(r"(\d+\.)\s*", r"\n\1 ", response_text)

    return formatted_text.strip()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def generate_response(request: QueryRequest):
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
