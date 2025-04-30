# Ancient DNA Analysis API

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/yourusername/ancient-dna-analysis/Run%20Tests)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.115.0-green)

A FastAPI-based API for analyzing ancient DNA sequences. Upload CSV files, generate DNA sequences, compare sequence similarities, and query API functionality using Gemini LLM.

## Features
- **CSV Upload**: Process sample data (`id`, `region`, `age`, `seed`) to generate and cache DNA sequences.
- **Sequence Retrieval**: Fetch cached sequences by sample ID.
- **Sequence Comparison**: Calculate similarity scores between sequences.
- **Natural Language Query**: Ask questions via `/ask-me-anything/`.
- **In-Memory Storage**: Uses `sequence_cache` with `sequence_cache.json` fallback.
- **Modular Code**: Split into `main.py` (API) and `utils.py` (utilities).

## Project Structure
```
├── main.py
├── utils.py
├── requirements.txt
├── sample.csv
├── sequence_cache.json
├── templates/
│   └── index.html
├── static/
└── .github/
    └── workflows/
        └── test.yml
```

## Prerequisites
- Python 3.11+
- Git
- Render account (for deployment)
- Google API key (for Gemini LLM)
- Csv File link : https://docs.google.com/spreadsheets/d/11_7rotOIU48oeZDY_jwu918tl_2fx2VpuEF7jGNOHZw/edit?usp=sharing
- Generate API :
  ```Enable Gemini API: Go to
      https://console.cloud.google.com/
  ```
    Create a new project (or select an existing one).
    Navigate to APIs & Services > Library.
    Search for "Gemini API" and click Enable.
- Create API Key :
    Go to APIs & Services > Credentials.
    Click Create Credentials > API Key.


## Installation

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

4. **Configure Environment**:
   Create `.env`:
   ```powershell
   echo GOOGLE_API_KEY=your-google-api-key > .env
   ```
   or
   ```
   $env:GOOGLE_API_KEY="your-google-api-key"
   ```

5. **Prepare Templates**:
   ```powershell
   mkdir templates
   mkdir static
   echo "<html><body><h1>Ancient DNA Analysis API</h1></body></html>" > templates/index.html
   ```

## Running Locally
```powershell
python main.py
```
- Access at `http://localhost:8000`.

## API Endpoints

| Endpoint                  | Method | Description                              | Example Payload                          |
|---------------------------|--------|------------------------------------------|------------------------------------------|
| `/`                       | GET    | Homepage (HTML)                         | -                                        |
| `/upload-csv/`            | POST   | Upload CSV and cache sequences          | Form: `file=@sample.csv`                 |
| `/generate-sequence/`     | POST   | Retrieve cached sequence                | `{"id": "id_0010"}`                     |
| `/compare-sequences/`     | POST   | Compare two sequences                   | `{"id1": "id_0010", "id2": "id_0011"}` |
| `/ask-me-anything/`       | POST   | Query API with natural language         | `{"question": "What does this API do?"}` |

## Usage

1. **Upload CSV**:
   ```powershell
   echo "id,region,age,seed" > sample.csv
   echo "id_0010,emea,1000,agtc" >> sample.csv
   curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
   ```

2. **Retrieve Sequence**:
   ```powershell
   curl -X POST http://localhost:8000/generate-sequence/ -H "Content-Type: application/json" -d "{\"id\": \"id_0010\"}"
   ```

3. **Compare Sequences**:
   ```powershell
   curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d "{\"id1\": \"id_0010\", \"id2\": \"id_0011\"}"
   ```

## Testing
```powershell
pytest tests.py
```
- Requires `sample.csv`.

## GitHub Actions
- **Workflow**: `.github/workflows/test.yml`
- **Triggers**: Push/pull requests to `main`.
- **Setup**:
  - Add `GOOGLE_API_KEY` to GitHub Secrets:
    - Go to Repository > Settings > Secrets and variables > Actions > New repository secret.
    - Name: `GOOGLE_API_KEY`, Value: your API key.

## Deployment on Render
1. **Push to GitHub**:
   ```powershell
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Configure Render**:
   - Create a Web Service.
   - Link to `ancient-dna-analysis`.
   - Settings:
     - Runtime: Python
     - Build: `pip install -r requirements.txt`
     - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Environment: `GOOGLE_API_KEY=your-google-api-key`

3. **Handle Cache**:
   - `sequence_cache.json` is ephemeral.
   - After `/upload-csv/`:
     ```powershell
     git add sequence_cache.json
     git commit -m "Update sequence_cache.json"
     git push origin main
     ```
   - Redeploy.

4. **Test**:
   ```powershell
   curl https://your-render-url.onrender.com/
   ```

## Persistent Storage (Optional)
For persistent storage:
1. Create a PostgreSQL database in Render.
2. Add `DATABASE_URL` to environment variables.
3. Update `requirements.txt`:
   ```powershell
   echo psycopg2-binary==2.9.9 >> requirements.txt
   ```
4. Modify `main.py` for PostgreSQL (see issues).

## Troubleshooting
- **Local**:
  - Check `sequence_cache.json`:
    ```powershell
    type sequence_cache.json
    ```
  - Verify sequence length:
    ```powershell
    type sequence_cache.json | jq '.id_0010.sequence | length'
    ```
  - Ensure `templates/index.html`.
- **Render**:
  - Check logs.
  - Verify `GOOGLE_API_KEY`.
- **GitHub Actions**:
  - Check Actions tab.
  - Confirm `GOOGLE_API_KEY`.

## Contributing
1. Fork the repository.
2. Create a branch: `git checkout -b feature-name`.
3. Commit: `git commit -m "Add feature"`.
4. Push: `git push origin feature-name`.
5. Open a pull request.

## License
MIT License. See [LICENSE](LICENSE).

## Contact
Open an issue on GitHub.
