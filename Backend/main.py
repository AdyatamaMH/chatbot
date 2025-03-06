from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class InputData(BaseModel):
    title: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

persist_directory = "./chroma.sqlite3"

