from fastapi import FastAPI, UploadFile, File, HTTPException
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

# In-memory storage for ancient remains data (use database in production)
ancient_remains: Dict[str, dict] = {}

# Pydantic models
class SequenceRequest(BaseModel):
    id: str

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

# Root endpoint
@app.get("/")
async def root():
    """Welcome message for the Ancient DNA Analysis API."""
    return {"message": "Welcome to the Ancient DNA Analysis API. Visit /docs for API documentation."}

# DNA sequence generation function
def generate_dna_sequence(id: str, region: str, age: int, dna_seed: str) -> str:
    """Generate a DNA sequence based on input parameters."""
    try:
        if not dna_seed or len(dna_seed) < 4:
            logger.error(f"Invalid seed for ID {id}: seed is empty or too short")
            raise ValueError("Seed must be at least 4 characters long")
        
        R.seed(f"{id}+{region}+{age}")

        def core():
            x = 1
            for _ in range(100_000):
                x = (x * 987654321) % 123456789
            return x

        Q = {
            "apac": ["agtc", "agct", "actg", "atgc", "actg", "agtc"],
            "na": ["gtac", "gcat", "gcta"],
            "latam": ["cgta", "ctga", "catg"],
            "emea": ["aagt", "aatg", "aagc"],
        }

        F = lambda S: list(
            {
                S[i : i + 4]
                for i in range(0, len(S) - 3, 4)
                if S[i : i + 4] in {q for v in Q.values() for q in v}
            }
        )

        L, T, C = [], 0, 1010101010

        while T < C:
            core()
            M = F(dna_seed)
            if not M:
                logger.warning(f"No valid motifs found for seed: {dna_seed[:50]}...")
                return "x"
            Z = R.choice(M)
            N = R.randint(10**3, 10**5)
            W = Z * N
            L.append(W)
            T += len(W)

        sequence = "".join(L)[:C]
        logger.info(f"Generated sequence for ID {id}, length: {len(sequence)}")
        return sequence
    except ValueError as ve:
        logger.error(f"ValueError generating sequence for ID {id}: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except MemoryError:
        logger.error(f"MemoryError generating sequence for ID {id}")
        raise HTTPException(status_code=500, detail="Memory error: Sequence generation too resource-intensive")
    except Exception as e:
        logger.error(f"Unexpected error generating sequence for ID {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sequence generation failed: {str(e)}")

# DNA sequence comparison function
def calculate_similarity(seq1: str, seq2: str) -> float:
    """Compare two DNA sequences and return a similarity score (0-100)."""
    try:
        if not seq1 or not seq2 or seq1 == "x" or seq2 == "x":
            logger.warning("One or both sequences are invalid or empty")
            return 0.0

        # Check for identical sequences
        if seq1 == seq2:
            logger.info("Sequences are identical, returning maximum similarity")
            return 100.0

        # Truncate sequences to manageable length for comparison
        max_compare_length = 5000  # Further reduced
        seq1 = seq1[:max_compare_length]
        seq2 = seq2[:max_compare_length]
        logger.info(f"Truncated sequences to {max_compare_length} bases for comparison")

        # Position-based similarity using difflib
        matcher = difflib.SequenceMatcher(None, seq1, seq2)
        position_score = matcher.ratio() * 50  # 50% weight
        logger.info(f"Position-based similarity score: {position_score}")

        # Motif-based similarity (4-mer matches)
        motif_length = 4
        motifs1 = {seq1[i:i+motif_length] for i in range(len(seq1) - motif_length + 1)}
        motifs2 = {seq2[i:i+motif_length] for i in range(len(seq2) - motif_length + 1)}
        common_motifs = motifs1.intersection(motifs2)
        if not motifs1 or not motifs2:
            logger.warning("One or both motif sets are empty")
            motif_score = 0.0
        else:
            motif_score = (len(common_motifs) / max(len(motifs1), len(motifs2))) * 50
        logger.info(f"Motif-based similarity score: {motif_score}")

        similarity = round(position_score + motif_score, 2)
        logger.info(f"Sequence comparison completed, similarity: {similarity}")
        return similarity
    except MemoryError:
        logger.error("MemoryError during sequence comparison")
        raise HTTPException(status_code=500, detail="Memory error: Sequence comparison too resource-intensive")
    except Exception as e:
        logger.error(f"Error comparing sequences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sequence comparison failed: {str(e)}")

# API Endpoints
@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and parse CSV file containing ancient remains data."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validate CSV columns
        required_columns = {'id', 'region', 'age', 'seed'}
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="CSV missing required columns")
        
        # Clean and store data efficiently
        for _, row in df.iterrows():
            id_val = str(row['id']).strip()
            region = str(row['region']).strip() if pd.notna(row['region']) else "Unknown"
            age = int(row['age']) if pd.notna(row['age']) else 0
            seed = str(row['seed']).strip() if pd.notna(row['seed']) else ""
            
            ancient_remains[id_val] = {
                'region': region,
                'age': age,
                'seed': seed
            }
        
        logger.info(f"Uploaded {len(df)} records")
        return {"message": f"Successfully uploaded {len(df)} records"}
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@app.post("/generate-sequence/")
async def generate_sequence(request: SequenceRequest):
    """Generate DNA sequence for a given sample ID."""
    if request.id not in ancient_remains:
        raise HTTPException(status_code=404, detail="Sample ID not found")
    
    sample = ancient_remains[request.id]
    sequence = generate_dna_sequence(
        request.id,
        sample['region'],
        sample['age'],
        sample['seed']
    )
    return {"id": request.id, "sequence": sequence[:1000]}  # Return first 1000 bases for response

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    """Compare DNA sequences of two samples."""
    try:
        if request.id1 not in ancient_remains:
            logger.error(f"Sample ID {request.id1} not found")
            raise HTTPException(status_code=404, detail=f"Sample ID {request.id1} not found")
        if request.id2 not in ancient_remains:
            logger.error(f"Sample ID {request.id2} not found")
            raise HTTPException(status_code=404, detail=f"Sample ID {request.id2} not found")
        
        # Generate sequences
        sample1 = ancient_remains[request.id1]
        sample2 = ancient_remains[request.id2]
        
        logger.info(f"Generating sequence for ID {request.id1}")
        seq1 = generate_dna_sequence(request.id1, sample1['region'], sample1['age'], sample1['seed'])
        logger.info(f"Generating sequence for ID {request.id2}")
        seq2 = generate_dna_sequence(request.id2, sample2['region'], sample2['age'], sample2['seed'])
        
        logger.info(f"Comparing sequences for IDs {request.id1} and {request.id2}")
        similarity = calculate_similarity(seq1, seq2)
        return {
            "id1": request.id1,
            "id2": request.id2,
            "similarity_score": similarity
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in compare-sequences endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/ask-me-anything/")
async def ask_me_anything(request: AskRequest):
    """Handle natural language questions about the API."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        prompt_template = PromptTemplate(
            input_variables=["question"],
            template="""
            You are an assistant for an Ancient DNA Analysis API. Provide clear, concise answers about the API's capabilities and usage.
            The API has endpoints for:
            - /upload-csv/: Upload CSV files with ancient remains data (id, region, age, seed)
            - /generate-sequence/: Generate DNA sequence for a sample ID
            - /compare-sequences/: Compare DNA sequences between two samples
            - /ask-me-anything/: Answer questions about the API
            
            Question: {question}
            Answer:
            """
        )
        
        chain = prompt_template | llm
        response = chain.invoke({"question": request.question})
        return {"answer": response.content}
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)