from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import io
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import logging
import sys
import utils

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
logger.handlers = [handler]
logger.setLevel(logging.INFO)

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

# Load sequence cache on startup
utils.load_cache()

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
    return templates.TemplateResponse(request, "index.html")

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
        skipped = 0
        max_rows = 5000
        for _, row in df.head(max_rows).iterrows():
            id_val = str(row['id']).strip()
            region = str(row['region']).strip() if pd.notna(row['region']) else "Unknown"
            try:
                age = int(row['age']) if pd.notna(row['age']) else 0
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid age for ID {id_val}: {row['age']}, skipping (error: {e})")
                skipped += 1
                continue
            seed = str(row['seed']).strip() if pd.notna(row['seed']) else ""
            logger.info(f"Processing sample ID: {id_val}")

            # Generate and cache sequence
            full_seq = utils.generate_dna_sequence(id_val, region, age, seed, MAX_CACHE_LEN)
            if full_seq == "x":
                logger.warning(f"Invalid sequence for ID {id_val}: seed={seed}, region={region}, age={age}")
                skipped += 1
                continue
            seq_to_store = full_seq[:MAX_CACHE_LEN]
            if len(seq_to_store) > MAX_CACHE_LEN:
                logger.warning(f"Sequence for ID {id_val} too long: {len(seq_to_store)}")
                seq_to_store = seq_to_store[:MAX_CACHE_LEN]
            logger.info(f"Sequence length for ID {id_val}: {len(seq_to_store)}")
            utils.sequence_cache[id_val] = {
                "id": id_val,
                "region": region,
                "age": age,
                "seed": seed,
                "sequence": seq_to_store
            }
            count += 1

        logger.info(f"sequence_cache before save: {list(utils.sequence_cache.keys())}")
        utils.save_cache()
        logger.info(f"Cached sequences for {count} samples, skipped {skipped} invalid rows")
        if len(df) > max_rows:
            return {
                "message": f"Processed {count} of {len(df)} records (limited to {max_rows}), skipped {skipped} invalid rows"
            }
        return {
            "message": f"Successfully uploaded and cached {count} records, skipped {skipped} invalid rows"
        }
    except Exception as e:
        logger.error(f"Error in upload_csv: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-sequence/")
async def generate_sequence(request: SequenceRequest):
    """
    Retrieve a cached DNA sequence for the given sample ID.
    """
    try:
        data = utils.sequence_cache.get(request.id)
        if not data:
            raise HTTPException(status_code=404, detail="Sample ID not found or sequence not generated")
        seq = data["sequence"]
        return {"id": request.id, "sequence": seq[:1000]}
    except Exception as e:
        logger.error(f"Error in generate_sequence for ID {request.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    """
    Compare two cached DNA sequences and return a similarity score.
    """
    try:
        data1 = utils.sequence_cache.get(request.id1)
        data2 = utils.sequence_cache.get(request.id2)
        if not data1 or not data2:
            raise HTTPException(status_code=404, detail="One or both sample IDs not found")
        seq1, seq2 = data1["sequence"], data2["sequence"]
        score = utils.calculate_similarity(seq1, seq2)
        return {"id1": request.id1, "id2": request.id2, "similarity_score": score}
    except Exception as e:
        logger.error(f"Error in compare_sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-me-anything/")
async def ask_me_anything(request: AskRequest):
    """
    Use Gemini LLM to answer natural language questions about the API.
    """
    logger.info(f"Received question: {request.question}")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))
        logger.info("Initialized ChatGoogleGenerativeAI")
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
        logger.info("Created PromptTemplate")
        chain = prompt | llm
        logger.info("Created LLM chain")
        response = chain.invoke({"question": request.question})
        logger.info(f"LLM response: {response.content}")
        return {"answer": response.content}
    except Exception as e:
        logger.error(f"Error in ask_me_anything: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
