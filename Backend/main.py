import json
import faiss
import numpy as np
import ollama
import re
from datetime import datetime
from fastapi import FastAPI, HTTPException
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

# Load FAISS index
INDEX_PATH = "csv_index.faiss"
index = faiss.read_index(INDEX_PATH)

# Load metadata
with open("csv_metadata.json", "r") as f:
    metadata = json.load(f)

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

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

def retrieve_context(query, top_k=102):
    """Retrieves relevant rows based on query embeddings and filters them dynamically."""
    query_embedding = embed_model.encode([query])
    query_embedding = normalize(query_embedding, norm='l2', axis=1)
    distances, indices = index.search(np.array(query_embedding), top_k)
    retrieved_rows = [metadata[idx] for idx in indices[0]]
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
    
    message = (
        f"On {context['business_date']}, at {context['business_unit']}, "
        f"the balance tier is {context['balance_tier_description']}, "
        f"with a total balance of {context['total_balance']:,.2f} IDR. "
        f"The number of customers in this tier is {context['no_of_customers']}."
    )
    
    return message

# Request model
class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def generate_response(request: QueryRequest):
    retrieved_context = retrieve_context(request.query)
    formatted_context = format_response(retrieved_context)
    
    input_text = f"Context: {formatted_context} \n Question: {request.query}"
    
    try:
        response = ollama.chat(model='mistral', messages=[{"role": "user", "content": input_text}])
        return {"response": response['message']['content'], "context": formatted_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
