Ancient DNA Analysis API
Overview
This FastAPI application provides endpoints for analyzing ancient remains DNA sequences. It supports uploading CSV files with remains data, generating DNA sequences using a provided function, comparing sequences, and answering natural language questions about the API.
Setup Instructions

Clone the Repository

git clone <repository-url>
cd ancient-dna-analysis


Install Dependencies

pip install fastapi uvicorn pandas langchain-google-genai python-dotenv


Set Up Environment VariablesCreate a .env file in the project root:

GOOGLE_API_KEY=your-google-api-key


Run the Server

python main.py

The server will run at http://localhost:8000.
API Endpoints

POST /upload-csv/

Upload a CSV file containing ancient remains data.
Required columns: id, region, age, seed
Example:curl -X POST -F "file=@CLEANED_DATA.csv" http://localhost:8000/upload-csv/




POST /generate-sequence/

Generate a DNA sequence for a given sample ID.
Request body: {"id": "id_0010"}
Example:curl -X POST -H "Content-Type: application/json" -d '{"id": "id_0010"}' http://localhost:8000/generate-sequence/




POST /compare-sequences/

Compare DNA sequences of two samples.
Request body: {"id1": "id_0010", "id2": "id_0011"}
Example:curl -X POST -H "Content-Type: application/json" -d '{"id1": "id_0010", "id2": "id_0011"}' http://localhost:8000/compare-sequences/




POST /ask-me-anything/

Ask questions about the API in natural language.
Request body: {"question": "What does this API do?"}
Example:curl -X POST -H "Content-Type: application/json" -d '{"question": "What does this API do?"}' http://localhost:8000/ask-me-anything/





DNA Sequence Generation

The generate_dna_sequence function (from func.py) generates a DNA sequence of 1,010,101,010 bases.
It uses a seeded random generator based on id, region, and age.
The function selects valid 4-mer motifs from the seed based on region-specific motif sets (Q) and repeats them randomly to create a long sequence.
If no valid motifs are found, it returns "x".

Sequence Comparison

The compare_sequences function calculates a similarity score (0-100) using:
Position-based similarity (50% weight): Uses difflib.SequenceMatcher to compute the ratio of matching bases.
Motif-based similarity (50% weight): Compares the overlap of 4-mer motifs between sequences.


Sequences are truncated to 100,000 bases for comparison to manage computational cost.
The score combines both metrics for a balanced assessment of similarity.

Performance Considerations

The sequence generation is computationally expensive due to the core() function's 100,000 iterations and the large output size.
Sequence comparison is optimized by limiting comparison length and using set operations for motif comparison.
In-memory storage is used for simplicity; a database (e.g., SQLite, PostgreSQL) is recommended for production to handle large datasets like CLEANED_DATA.csv.

Error Handling

Invalid CSV files or missing columns raise 400 errors.
Non-existent sample IDs raise 404 errors.
Sequence generation or comparison failures raise 500 errors with detailed messages.
Logging is implemented to track errors and key operations.

Testing

Create a tests.py file with unit tests for:
CSV upload validation
Sequence generation for known inputs
Sequence comparison with identical and different sequences


Test with CLEANED_DATA.csv using sample IDs like id_0010 and id_0011.
Example test command (after creating tests):pytest tests.py



Deployment
To deploy on Vercel:

Install Vercel CLI: npm i -g vercel
Create a vercel.json file:{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}


Run: vercel
Follow prompts to deploy.

GitHub Repository
Link to repository : https://github.com/Hasin02/ancient-dna-analysis.git
Notes

The Google API key is required for the /ask-me-anything/ endpoint.
The CLEANED_DATA.csv file contains large seed strings; ensure sufficient memory when processing.
For production, implement caching (e.g., Redis) for generated sequences to reduce computation time.
Consider database storage for large datasets and persistent data.