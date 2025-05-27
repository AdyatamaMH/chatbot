# AI Chatbot with MySQL & CSV Data Support

This project is a full-stack chatbot interface that allows users to interact with MySQL databases and uploaded CSV files using natural language which in this case uses Mistral. The backend uses FastAPI and Ollama with Mistral for LLM responses, and supports both dynamic charting and static graph generation via `matplotlib`.

---

## ✨ Features

- ✅ Natural language interface for MySQL or CSV data
- ✅ MySQL table/row selection and RAG-like AI context summarization
- ✅ Upload and query CSV files (FAISS-based vector search)
- ✅ User-controlled MySQL credentials input via frontend

---

## Frontend Dependencies

Make sure you have:
- Node.js (v14+)
- React

Install frontend dependencies:
```bash
npm install
```
Then run:
```bash
npm run dev
```
note you need to cd to the frontend folder

## Backend Dependencies

Install via pip:

```bash
pip install fastapi uvicorn pydantic python-multipart mysql-connector-python pandas matplotlib sentence-transformers scikit-learn faiss-cpu requests python-dotenv
```
Start the backend server using Uvicorn:

```bash
uvicorn main4:app --reload
```
Make sure this runs in the same directory as your main4.py file.