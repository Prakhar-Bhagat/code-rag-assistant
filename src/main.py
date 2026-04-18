from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import shutil
import os
from dotenv import load_dotenv

# Rate Limiting Imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .ingestion import IngestionPipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_groq import ChatGroq

load_dotenv()

# --- SECURITY & RATE LIMITING SETUP ---
limiter = Limiter(key_func=get_remote_address)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "default-dev-key")

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != BACKEND_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key. Access Denied.")
    return api_key
# --------------------------------------

app = FastAPI(title="CodeRAG API (Secured)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

pipeline = IngestionPipeline()
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("API_KEY"))

@app.get("/health")
def health_check():
    return {"status": "healthy", "secured": True}

# Add 'Depends(get_api_key)' to lock this route down
@app.post("/ingest", dependencies=[Depends(get_api_key)])
@limiter.limit("5/minute") # Rate limit: Max 5 uploads per minute
async def ingest_code(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    temp_zip = f"temp_{file.filename}"
    with open(temp_zip, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    background_tasks.add_task(process_and_cleanup, temp_zip)
    return {"message": f"Ingestion of {file.filename} started in background."}

def process_and_cleanup(zip_path):
    extract_folder = "./extracted_repo"
    try:
        pipeline.unzip_repo(zip_path, extract_folder)
        pipeline.process_directory(extract_folder)
    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(extract_folder): shutil.rmtree(extract_folder)

class QueryRequest(BaseModel):
    question: str

# Lock down the query route and limit to 10 requests per minute
@app.post("/query", dependencies=[Depends(get_api_key)])
@limiter.limit("10/minute") 
async def query_code(request: Request, query_req: QueryRequest):
    system_instructions = (
        "You are an expert backend developer assistant analyzing a codebase. "
        "Answer the user's question DIRECTLY using the provided context. "
        "You are allowed to logically infer architectural intent, flows, and concepts from class names, variable names, and docstrings in the context. "
        "Do NOT generate extra questions. Do NOT use outside knowledge. "
        "If the answer cannot be reasonably deduced from the provided code, say 'I cannot find the answer in the provided code.'\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", "{input}")
    ])
    
    retriever = pipeline.get_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    response = rag_chain.invoke({"input": query_req.question})
    
    sources = list(set([doc.metadata.get("source", "Unknown file") for doc in response.get("context", [])]))
            
    return {"answer": response["answer"], "citations": sources}