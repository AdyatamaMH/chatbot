from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from dotenv import load_dotenv


load_dotenv()

# Database Configuration
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
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        return None


@app.get("/get_mysql_data")
def get_mysql_data():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, column1, column2, column3 FROM your_table"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return data


@app.post("/query_mysql")
def query_mysql(query: dict):
    user_query = query.get("query", "")
    selected_rows = query.get("selectedRows", [])

    if not user_query:
        raise HTTPException(status_code=400, detail="Query is empty")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(user_query)
        result = cursor.fetchall()
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail=str(err))
    
    cursor.close()
    conn.close()
    
    return {"response": result}
