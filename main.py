from fastapi import FastAPI, Request, UploadFile, File, HTTPException, BackgroundTasks
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

# Constants
MAX_CACHE_LEN = 5000

# Pydantic models
class SequenceRequest(BaseModel):
    id: str

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...), background_tasks: BackgroundTasks):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        required_columns = {'id', 'region', 'age', 'seed'}
        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail="CSV missing required columns")

        background_tasks.add_task(process_csv_async, df.to_dict("records"))
        return {"message": "Upload received. Processing in background."}
    except Exception as e:
        logger.error(f"Error in upload_csv: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def process_csv_async(records):
    count = 0
    skipped = 0
    for row in records:
        try:
            id_val = str(row['id']).strip()
            region = str(row['region']).strip() if row['region'] else "Unknown"
            age = int(row['age']) if row['age'] else 0
            seed = str(row['seed']).strip() if row['seed'] else ""
        except Exception as e:
            logger.warning(f"Skipping invalid row: {row}")
            skipped += 1
            continue

        full_seq = utils.generate_dna_sequence(id_val, region, age, seed, MAX_CACHE_LEN)
        if full_seq == "x":
            logger.warning(f"Invalid sequence for ID {id_val}")
            skipped += 1
            continue

        utils.sequence_cache[id_val] = {
            "id": id_val,
            "region": region,
            "age": age,
            "seed": seed,
            "sequence": full_seq[:MAX_CACHE_LEN]
        }
        count += 1

    logger.info(f"Finished background processing: {count} saved, {skipped} skipped")
    utils.save_cache()

@app.post("/generate-sequence/")
async def generate_sequence(request: SequenceRequest):
    try:
        data = utils.sequence_cache.get(request.id)
        if not data:
            raise HTTPException(status_code=404, detail="Sample ID not found or sequence not generated")
        return {"id": request.id, "sequence": data["sequence"][:1000]}
    except Exception as e:
        logger.error(f"Error in generate_sequence for ID {request.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    try:
        data1 = utils.sequence_cache.get(request.id1)
        data2 = utils.sequence_cache.get(request.id2)
        if not data1 or not data2:
            raise HTTPException(status_code=404, detail="One or both sample IDs not found")
        score = utils.calculate_similarity(data1["sequence"], data2["sequence"])
        return {"id1": request.id1, "id2": request.id2, "similarity_score": score}
    except Exception as e:
        logger.error(f"Error in compare_sequences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-me-anything/")
async def ask_me_anything(request: AskRequest):
    logger.info(f"Received question: {request.question}")
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
        logger.error(f"Error in ask_me_anything: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
