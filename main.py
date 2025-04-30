from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import io
import random as R
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import difflib
import logging

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

# In-memory sequence cache
sequence_cache = {}

# Load sequence cache from JSON file if it exists
CACHE_FILE = "sequence_cache.json"
def load_cache():
    global sequence_cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                sequence_cache = json.load(f)
            logger.info(f"Loaded {len(sequence_cache)} sequences from {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Error loading cache: {e}")

# Save sequence cache to JSON file
def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(sequence_cache, f)
        logger.info(f"Saved {len(sequence_cache)} sequences to {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

# Load cache on startup
load_cache()

# Pydantic models
class SequenceRequest(BaseModel):
    id: str

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

# Define a maximum sequence length to store
MAX_CACHE_LEN = 5000

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
        max_rows = 5000  # Increased for more data processing
        for _, row in df.head(max_rows).iterrows():
            id_val = str(row['id']).strip()
            region = str(row['region']).strip() if pd.notna(row['region']) else "Unknown"
            age = int(row['age']) if pd.notna(row['age']) else 0
            seed = str(row['seed']).strip() if pd.notna(row['seed']) else ""
            logger.info(f"Processing sample ID: {id_val}")

            # Generate and cache sequence
            full_seq = generate_dna_sequence(id_val, region, age, seed)
            if full_seq == "x":
                logger.warning(f"Invalid sequence for ID: {id_val}")
                continue
            seq_to_store = full_seq[:MAX_CACHE_LEN]
            if len(seq_to_store) > MAX_CACHE_LEN:
                logger.warning(f"Sequence for ID {id_val} too long: {len(seq_to_store)}")
                seq_to_store = seq_to_store[:MAX_CACHE_LEN]
            logger.info(f"Sequence length for ID {id_val}: {len(seq_to_store)}")
            sequence_cache[id_val] = {
                "id": id_val,
                "region": region,
                "age": age,
                "seed": seed,
                "sequence": seq_to_store
            }
            count += 1

        save_cache()  # Save cache to JSON file
        logger.info(f"Cached sequences for {count} samples")
        if len(df) > max_rows:
            return {"message": f"Processed {count} of {len(df)} records (limited to {max_rows})"}
        return {"message": f"Successfully uploaded and cached {count} records"}
    except Exception as e:
        logger.error(f"Error in upload_csv: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-sequence/")
async def generate_sequence(request: SequenceRequest):
    """
    Retrieve a cached DNA sequence for the given sample ID.
    """
    try:
        data = sequence_cache.get(request.id)
        if not data:
            raise HTTPException(status_code=404, detail="Sample ID not found or sequence not generated")
        seq = data["sequence"]
        return {"id": request.id, "sequence": seq[:1000]}  # Return only the first 1000 characters
    except Exception as e:
        logger.error(f"Error in generate_sequence for ID {request.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    """
    Compare two cached DNA sequences and return a similarity score.
    """
    try:
        data1 = sequence_cache.get(request.id1)
        data2 = sequence_cache.get(request.id2)
        if not data1 or not data2:
            raise HTTPException(status_code=404, detail="One or both sample IDs not found")
        seq1, seq2 = data1["sequence"], data2["sequence"]
        score = calculate_similarity(seq1, seq2)
        return {"id1": request.id1, "id2": request.id2, "similarity_score": score}
    except Exception as e:
        logger.error(f"Error in compare_sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            logger.warning(f"Invalid seed for ID {id}")
            return "x"
        R.seed(f"{id}+{region}+{age}")
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
            logger.warning(f"No valid motifs for ID {id}")
            return "x"
        L, total, max_len = [], 0, 5000
        while total < max_len:
            z = R.choice(motifs)
            n = R.randint(10, 50)
            w = z * n
            if total + len(w) > max_len:
                w = w[:max_len - total]
            L.append(w)
            total += len(w)
        seq = "".join(L)
        logger.info(f"Generated sequence length for ID {id}: {len(seq)}")
        if len(seq) > MAX_CACHE_LEN:
            logger.warning(f"Sequence too long for ID {id}: {len(seq)}")
            seq = seq[:MAX_CACHE_LEN]
        return seq
    except Exception as e:
        logger.error(f"Error in generate_dna_sequence for ID {id}: {e}")
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
