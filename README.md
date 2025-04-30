# 🧬 Ancient DNA Analysis API

This **FastAPI** application allows forensic researchers to analyze ancient DNA data. It supports:

- 📄 Uploading CSV files with ancient remains data
- 🧬 Generating full DNA sequences using a custom logic
- 🔬 Comparing two DNA sequences for similarity
- 💬 Asking natural language questions about the API using Google Gemini

---

## 🚀 Setup Instructions

### CSV FILE 
Link:
```
https://docs.google.com/spreadsheets/d/11_7rotOIU48oeZDY_jwu918tl_2fx2VpuEF7jGNOHZw/edit?usp=sharing
```

### 1. Clone the Repository

```
git clone https://github.com/Hasin02/ancient-dna-analysis.git
cd ancient-dna-analysis
```
2. Create a Virtual Environment
```
python -m venv venv
.\venv\Scripts\activate  # For Windows
```
3. Install Dependencies: 
```
pip install -r requirements.txt  
```

4. Run the Server
```
python main.py
```
The server will run at http://localhost:8000
Open http://localhost:8000/docs

🔌 API Endpoints


📤 POST /upload-csv/


Upload a CSV file containing ancient remains data.

Required Columns: id, region, age, seed
```
curl -X POST -F "file=@CLEANED_DATA.csv" http://localhost:8000/upload-csv/

```


🧬 POST /generate-sequence/
Generate a DNA sequence for a given sample ID.

Request Body:
```
{ "id": "id_0010" }
```
Example:
```
curl -X POST -H "Content-Type: application/json" -d '{"id": "id_0010"}' http://localhost:8000/generate-sequence/
```



🔍 POST /compare-sequences/
Compare DNA sequences of two samples.

Request Body:
```
{"id1": "id_0010", "id2": "id_0011"}
```
Example:
```
curl -X POST -H "Content-Type: application/json" -d '{"id1": "id_0010", "id2": "id_0011"}' http://localhost:8000/compare-sequences/
```



🤖 POST /ask-me-anything/
Ask natural language questions about how the API works.

Request Body:
```
{"question": "What does this API do?"}
```
Example:
```
curl -X POST -H "Content-Type: application/json" -d '{"question": "What does this API do?"}' http://localhost:8000/ask-me-anything/
```




🧠 How DNA Sequence Generation Works
The DNA sequence is generated using a function in func.py:

It uses a seeded random generator based on ID, region, and age

Extracts valid 4-letter DNA motifs from the seed

Randomly repeats them until a long sequence (~1 billion bases) is generated

If no valid motifs are found in the seed, it returns "x"

🔗 How Sequence Comparison Works
The similarity score (0–100) is based on:

🔢 Position-based match (50% weight): Uses difflib.SequenceMatcher

🔠 Motif-based match (50% weight): Compares 4-letter substring overlap

To improve performance:

Sequences are truncated (e.g., first 100,000 characters)

Set operations are used for fast motif comparison

⚙️ Performance Notes
DNA generation is CPU-heavy (due to many loop iterations)

Sequence comparison is optimized, but still resource-intensive

Data is stored in-memory for simplicity (not ideal for large datasets)

Consider using:

✅ Caching with Redis

✅ SQLite/PostgreSQL for persistent storage

❗ Error Handling
🚫 400 – Invalid CSV file or missing columns

🔍 404 – Sample ID not found

💥 500 – Sequence generation/comparison failure (e.g., memory issue)

Logging is implemented to help debug issues.

🧪 Testing
Create a tests.py to test:

CSV upload validation

DNA sequence generation

Sequence comparison logic
```
pytest tests.py
```
Test IDs like id_0010 and id_0011 using your CLEANED_DATA.csv.

GitHub Repository
Link to repository : https://github.com/Hasin02/ancient-dna-analysis.git
Notes

The Google API key is required for the /ask-me-anything/ endpoint.
The CLEANED_DATA.csv file contains large seed strings; ensure sufficient memory when processing.
For production, implement caching (e.g., Redis) for generated sequences to reduce computation time.
Consider database storage for large datasets and persistent data.
