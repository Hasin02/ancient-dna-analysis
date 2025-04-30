from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import io
from typing import Dict
import random as R
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import difflib
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ancient DNA Analysis API",
    description="API for analyzing ancient remains DNA sequences",
    version="1.0.0"
)

# Load environment variables
load_dotenv()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# SQLite database setup
conn = sqlite3.connect('dna_sequences.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS sequences (
        id TEXT PRIMARY KEY,
        region TEXT,
        age INTEGER,
        seed TEXT,
        sequence TEXT
    )
    '''
)
conn.commit()

# Pydantic models
class SequenceRequest(BaseModel):
    id: str

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV, generate and cache DNA sequences for each sample.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        required_columns = {'id', 'region', 'age', 'seed'}
        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail="CSV missing required columns")

        count = 0
        for _, row in df.iterrows():
            id_val = str(row['id']).strip()
            region = str(row['region']).strip() if pd.notna(row['region']) else "Unknown"
            age = int(row['age']) if pd.notna(row['age']) else 0
            seed = str(row['seed']).strip() if pd.notna(row['seed']) else ""

            # Generate and cache sequence
            seq = generate_dna_sequence(id_val, region, age, seed)
            cursor.execute(
                "INSERT OR REPLACE INTO sequences (id, region, age, seed, sequence) VALUES (?, ?, ?, ?, ?)",
                (id_val, region, age, seed, seq)
            )
            count += 1

        conn.commit()
        logger.info(f"Cached sequences for {count} samples")
        return {"message": f"Successfully uploaded and cached {count} records"}
    except Exception as e:
        logger.error(f"Error in upload_csv: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-sequence/")
async def generate_sequence(request: SequenceRequest):
    """
    Retrieve a cached DNA sequence for the given sample ID.
    """
    cursor.execute("SELECT sequence FROM sequences WHERE id = ?", (request.id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sample ID not found or sequence not generated")
    seq = row[0]
    return {"id": request.id, "sequence": seq[:1000]}

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    """
    Compare two cached DNA sequences and return a similarity score.
    """
    cursor.execute("SELECT sequence FROM sequences WHERE id = ?", (request.id1,))
    row1 = cursor.fetchone()
    cursor.execute("SELECT sequence FROM sequences WHERE id = ?", (request.id2,))
    row2 = cursor.fetchone()
    if not row1 or not row2:
        raise HTTPException(status_code=404, detail="One or both sample IDs not found")
    seq1, seq2 = row1[0], row2[0]
    score = calculate_similarity(seq1, seq2)
    return {"id1": request.id1, "id2": request.id2, "similarity_score": score}

@app.post("/ask-me-anything/")
async def ask_me_anything(request: AskRequest):
    """
    Use Gemini LLM to answer natural language questions about the API.
    """
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))
        prompt = PromptTemplate(
            input_variables=["question"],
            template="""
You are an assistant for the Ancient DNA Analysis API. The API supports:
- /upload-csv/: Upload CSV and cache sequences
- /generate-sequence/: Retrieve cached sequence
- /compare-sequences/: Compare two sequences
- /ask-me-anything/: Answer API usage questions

Question: {question}
Answer:
"""
        )
        chain = prompt | llm
        response = chain.invoke({"question": request.question})
        return {"answer": response.content}
    except Exception as e:
        logger.error(f"Error in ask-me-anything: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility functions
def generate_dna_sequence(id: str, region: str, age: int, dna_seed: str) -> str:
    try:
        if not dna_seed or len(dna_seed) < 4:
            return "x"
        R.seed(f"{id}+{region}+{age}")
        def core():
            x = 1
            for _ in range(100_000):
                x = (x * 987654321) % 123456789
            return x
        Q = {
            "apac": ["agtc", "agct", "actg", "atgc"],
            "na": ["gtac", "gcat", "gcta"],
            "latam": ["cgta", "ctga", "catg"],
            "emea": ["aagt", "aatg", "aagc"],
        }
        motifs = [
            dna_seed[i:i+4]
            for i in range(0, len(dna_seed) - 3, 4)
            if dna_seed[i:i+4] in {m for v in Q.values() for m in v}
        ]
        if not motifs:
            return "x"
        L, total, max_len = [], 0, 1010101010
        while total < max_len:
            core()
            z = R.choice(motifs)
            n = R.randint(10**3, 10**5)
            w = z * n
            L.append(w)
            total += len(w)
        return "".join(L)[:max_len]
    except:
        return "x"

def calculate_similarity(seq1: str, seq2: str) -> float:
    if not seq1 or not seq2 or seq1 == "x" or seq2 == "x":
        return 0.0
    if seq1 == seq2:
        return 100.0
    s1, s2 = seq1[:5000], seq2[:5000]
    pos_score = difflib.SequenceMatcher(None, s1, s2).ratio() * 50
    m1 = {s1[i:i+4] for i in range(len(s1) - 3)}
    m2 = {s2[i:i+4] for i in range(len(s2) - 3)}
    common = m1 & m2
    motif_score = (len(common) / max(len(m1), len(m2))) * 50 if m1 and m2 else 0.0
    return round(pos_score + motif_score, 2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
