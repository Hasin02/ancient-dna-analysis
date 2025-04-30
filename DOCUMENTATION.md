# Ancient DNA Analysis API Documentation

## Overview

The Ancient DNA Analysis API is a FastAPI-based web application designed to process, generate, and analyze ancient DNA sequences. It enables users to upload CSV files containing sample data, generate DNA sequences, retrieve cached sequences, compare sequences for similarity, and query API functionality using natural language via the Gemini language model. The project is optimized for local development and cloud deployment, with a modular codebase and in-memory storage for efficient sequence management.

### Key Features
- **CSV Upload**: Processes CSV files with sample data (`id`, `region`, `age`, `seed`) to generate and cache DNA sequences.
- **Sequence Generation**: Generates DNA sequences based on sample attributes and caches them in memory.
- **Sequence Comparison**: Calculates similarity scores between two sequences using motif and positional analysis.
- **Natural Language Query**: Answers API-related questions using Gemini LLM via `/ask-me-anything/`.
- **In-Memory Storage**: Stores sequences in a dictionary (`sequence_cache`) with a JSON file (`sequence_cache.json`) for persistence.
- **Modular Design**: Separates API logic (`main.py`) from utilities (`utils.py`) for maintainability.

### Use Cases
- Researchers analyzing ancient DNA samples.
- Developers building tools for genetic data processing.
- Educators demonstrating DNA sequence analysis workflows.

## Project Architecture

### Technology Stack
- **Backend**: FastAPI (0.115.0), Python (3.11)
- **Dependencies**: pandas (2.2.2), langchain-google-genai (1.0.10), python-dotenv (1.0.1), uvicorn (0.30.6), pytest (8.3.3), python-multipart (0.0.12)
- **Storage**: In-memory dictionary (`sequence_cache`) with JSON file (`sequence_cache.json`) fallback
- **Frontend**: Jinja2 templates (`index.html`) for basic UI
- **External Services**: Google Gemini API for natural language processing
- **CI/CD**: GitHub Actions for automated testing
- **Deployment**: Render for cloud hosting

### File Structure
```
├── main.py                 # FastAPI app, endpoints, and core logic
├── utils.py               # Utility functions (sequence generation, similarity, cache management)
├── requirements.txt       # Python dependencies
├── sample.csv             # Sample CSV for testing
├── sequence_cache.json    # Runtime cache file
├── templates/
│   └── index.html         # Homepage template
├── static/                # Static assets (CSS, JS)
├── tests.py              # Unit tests
├── README.md             # Project overview and setup
├── LICENSE               # MIT License
└── .github/
    └── workflows/
        └── test.yml       # GitHub Actions workflow
```

### Codebase Overview
- **`main.py`**:
  - Defines the FastAPI application and mounts static files/templates.
  - Implements endpoints: `/`, `/upload-csv/`, `/generate-sequence/`, `/compare-sequences/`, `/ask-me-anything/`.
  - Handles CSV parsing, sequence caching, and Gemini LLM integration.
  - Uses Pydantic models for request validation (`SequenceRequest`, `CompareRequest`, `AskRequest`).
- **`utils.py`**:
  - Contains helper functions:
    - `load_cache()`: Loads `sequence_cache.json` into `sequence_cache`.
    - `save_cache()`: Saves `sequence_cache` to `sequence_cache.json`.
    - `generate_dna_sequence()`: Generates DNA sequences using motifs and random repetition.
    - `calculate_similarity()`: Computes similarity scores using difflib and motif overlap.
  - Manages the global `sequence_cache` dictionary.
- **Storage**:
  - In-memory `sequence_cache` stores sequences as dictionaries `{id: {id, region, age, seed, sequence}}`.
  - Sequences are truncated to `MAX_CACHE_LEN = 5000` characters.
  - `sequence_cache.json` provides a fallback for persistence, updated after each `/upload-csv/`.

## Setup

### Prerequisites
- Python 3.11+
- Git
- Render account (for deployment)
- Google Cloud account for Gemini API key

### Installation

1. **Clone the Repository**:
   ```powershell
   git clone https://github.com/yourusername/ancient-dna-analysis.git
   cd ancient-dna-analysis
   ```

2. **Set Up Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure Google API Key**:
   - Enable Gemini API:
     - Go to [Google Cloud Console](https://console.cloud.google.com/).
     - Create a new project or select an existing one.
     - Navigate to **APIs & Services** > **Library**.
     - Search for "Gemini API" and click **Enable**.
   - Create API Key:
     - Go to **APIs & Services** > **Credentials**.
     - Click **Create Credentials** > **API Key**.
     - Copy the key and add it to `.env`:
       ```powershell
       echo GOOGLE_API_KEY=your-api-key > .env
       ```

5. **Prepare Templates and Static Files**:
   ```powershell
   mkdir templates
   mkdir static
   echo "<html><body><h1>Ancient DNA Analysis API</h1></body></html>" > templates/index.html
   ```

### Running Locally
```powershell
python main.py
```
- Access the API at `http://localhost:8000`.
- The homepage (`/`) renders `templates/index.html`.

## API Endpoints

| Endpoint                  | Method | Description                              | Request Body/Parameters                  | Response Example                         |
|---------------------------|--------|------------------------------------------|------------------------------------------|------------------------------------------|
| `/`                       | GET    | Renders homepage (HTML)                 | -                                        | HTML page                                |
| `/upload-csv/`            | POST   | Uploads CSV, generates/caches sequences | Form: `file` (CSV file)                  | `{"message": "Processed 2 records"}`     |
| `/generate-sequence/`     | POST   | Retrieves cached sequence by ID         | `{"id": "id_0010"}`                     | `{"id": "id_0010", "sequence": "agtc..."}` |
| `/compare-sequences/`     | POST   | Compares two sequences                  | `{"id1": "id_0010", "id2": "id_0011"}` | `{"id1": "id_0010", "id2": "id_0011", "similarity_score": 85.5}` |
| `/ask-me-anything/`       | POST   | Answers API questions via Gemini LLM    | `{"question": "What does this API do?"}` | `{"answer": "This API analyzes..."}`     |

### CSV Format
The CSV file must include:
- Columns: `id` (string), `region` (string), `age` (integer), `seed` (string, min 4 chars).
- Example (`sample.csv`):
  ```csv
  id,region,age,seed
  id_0010,emea,1000,agtc
  id_0011,emea,1000,agtc
  ```

### Example Workflow
1. **Upload CSV**:
   ```powershell
   echo "id,region,age,seed" > sample.csv
   echo "id_0010,emea,1000,agtc" >> sample.csv
   curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
   ```
   - Generates sequences, caches them in `sequence_cache`, and saves to `sequence_cache.json`.

2. **Retrieve Sequence**:
   ```powershell
   curl -X POST http://localhost:8000/generate-sequence/ -H "Content-Type: application/json" -d "{\"id\": \"id_0010\"}"
   ```
   - Returns the first 1000 characters of the sequence.

3. **Compare Sequences**:
   ```powershell
   curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d "{\"id1\": \"id_0010\", \"id2\": \"id_0011\"}"
   ```
   - Returns a similarity score (0–100).

4. **Query API**:
   ```powershell
   curl -X POST http://localhost:8000/ask-me-anything/ -H "Content-Type: application/json" -d "{\"question\": \"What does this API do?\"}"
   ```
   - Returns a natural language response.

## Testing

### Unit Tests
- File: `tests.py`
- Tests endpoints using `sample.csv` and FastAPI’s `TestClient`.
- Run tests:
  ```powershell
  pytest tests.py
  ```

### Test Cases
- `test_root_endpoint`: Verifies `/` returns 200.
- `test_upload_csv_endpoint`: Tests CSV upload and caching.
- `test_generate_sequence_endpoint`: Checks sequence retrieval.
- `test_compare_sequences_endpoint`: Validates similarity scores.
- `test_ask_me_anything_endpoint`: Tests Gemini LLM response.

## CI/CD with GitHub Actions

- **Workflow**: `.github/workflows/test.yml`
- **Triggers**: Push/pull requests to `main`.
- **Steps**:
  - Sets up Python 3.11.
  - Installs dependencies from `requirements.txt`.
  - Runs `pytest tests.py`.
- **Configuration**:
  - Add `GOOGLE_API_KEY` to GitHub Secrets:
    - Repository > Settings > Secrets and variables > Actions > New repository secret.
    - Name: `GOOGLE_API_KEY`, Value: your API key.

## Deployment on Render

### Steps
1. **Push to GitHub**:
   ```powershell
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Configure Render**:
   - Create a Web Service in Render.
   - Link to `ancient-dna-analysis` repository.
   - Settings:
     - Runtime: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Environment Variables:
       - `GOOGLE_API_KEY=your-google-api-key`

3. **Handle Cache Persistence**:
   - Render’s filesystem is ephemeral, so `sequence_cache.json` is lost on restart.
   - After `/upload-csv/`:
     ```powershell
     cd C:\Users\hasin\OneDrive\Desktop\ss\test-ancient-dna
     copy sequence_cache.json C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
     cd C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
     git add sequence_cache.json
     git commit -m "Update sequence_cache.json"
     git push origin main
     ```
   - Redeploy to include `sequence_cache.json`.

4. **Test Deployment**:
   ```powershell
   curl https://your-render-url.onrender.com/
   curl -X POST -F "file=@sample.csv" https://your-render-url.onrender.com/upload-csv/
   ```

### Notes
- `sequence_cache.json` persistence requires manual Git commits or a persistent database.
- Maximum rows processed: 5000 (`max_rows = 5000`).
- Sequence length capped at 5000 characters (`MAX_CACHE_LEN = 5000`).

## Persistent Storage (Optional)

To address Render’s ephemeral filesystem, use Render’s PostgreSQL database for persistent storage.

### Steps
1. **Create PostgreSQL Database**:
   - In Render dashboard, create a PostgreSQL database.
   - Copy the database URL (e.g., `postgresql://user:password@host:port/dbname`).
   - Add to Render environment variables as `DATABASE_URL`.

2. **Update Dependencies**:
   ```powershell
   echo psycopg2-binary==2.9.9 >> requirements.txt
   ```

3. **Modify `main.py`**:
   - Replace `sequence_cache` with PostgreSQL queries.
   - Example (partial code):
     ```python
     import psycopg2
     from psycopg2.extras import RealDictCursor

     conn = psycopg2.connect(os.getenv("DATABASE_URL"))
     cursor = conn.cursor(cursor_factory=RealDictCursor)
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
     ```
   - Update `/upload-csv/` to insert sequences into the database.
   - Update `/generate-sequence/` and `/compare-sequences/` to query the database.

4. **Redeploy**:
   ```powershell
   git add main.py requirements.txt
   git commit -m "Add PostgreSQL support"
   git push origin main
   ```

## Maintenance

### Monitoring
- **Logs**: Check FastAPI logs for errors (`logging.INFO` level).
- **Cache Size**: Monitor `sequence_cache.json` size; sequences are capped at 5000 characters.
- **Render Logs**: Review deployment logs for runtime issues.

### Updates
- **Dependencies**: Update `requirements.txt` with `pip install --upgrade -r requirements.txt`.
- **Gemini API**: Ensure `GOOGLE_API_KEY` remains valid; rotate if compromised.
- **Codebase**: Add new endpoints or features in `main.py` or `utils.py` as needed.

### Scaling
- Increase `max_rows` or `MAX_CACHE_LEN` in `main.py` for larger datasets (monitor memory usage).
- Migrate to PostgreSQL for production-grade persistence.
- Add authentication for secure API access.

## Troubleshooting

### Common Issues
- **Local**:
  - **Error**: `sequence_cache.json` not found.
    - **Fix**: Run `/upload-csv/` to generate it.
    - **Check**:
      ```powershell
      type sequence_cache.json
      ```
  - **Error**: Sequence length exceeds 5000.
    - **Fix**: Verify truncation in `utils.py`.
    - **Check**:
      ```powershell
      type sequence_cache.json | jq '.id_0010.sequence | length'
      ```
  - **Error**: `templates/index.html` missing.
    - **Fix**:
      ```powershell
      echo "<html><body><h1>Ancient DNA Analysis API</h1></body></html>" > templates/index.html
      ```
- **Render**:
  - **Error**: `GOOGLE_API_KEY` invalid.
    - **Fix**: Verify key in Render environment variables.
  - **Error**: Sequences lost on restart.
    - **Fix**: Commit `sequence_cache.json` or use PostgreSQL.
- **GitHub Actions**:
  - **Error**: Tests fail due to missing `GOOGLE_API_KEY`.
    - **Fix**: Add key to GitHub Secrets.

### Debugging
- Check logs in `main.py` and `utils.py` for errors.
- Test endpoints individually:
  ```powershell
  curl http://localhost:8000/
  curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
  ```

## Contributing

1. Fork the repository.
2. Create a feature branch:
   ```powershell
   git checkout -b feature-name
   ```
3. Commit changes:
   ```powershell
   git commit -m "Add feature"
   ```
4. Push to branch:
   ```powershell
   git push origin feature-name
   ```
5. Open a pull request on GitHub.

## License
MIT License. See [LICENSE](LICENSE) for details.

## Contact
For issues, suggestions, or contributions, open an issue on [GitHub](https://github.com/yourusername/ancient-dna-analysis).
