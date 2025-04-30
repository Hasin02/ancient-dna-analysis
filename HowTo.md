# How to Run the Server, Upload Files, and Interact with the Ancient DNA Analysis API

This guide explains how to run the Ancient DNA Analysis API server, upload CSV files to generate DNA sequences, and interact with the API endpoints. It is designed for users and developers working with the API locally or on a deployed Render instance.

## Prerequisites
- Python 3.11+
- Git
- Google API key (for `/ask-me-anything/` endpoint)
- Render account (for cloud deployment)
- Project files: `main.py`, `utils.py`, `requirements.txt`, `templates/index.html`, `sample.csv`

## 1. Running the Server

### Locally
1. **Navigate to Project Directory**:
   ```powershell
   cd C:\Users\hasin\OneDrive\Desktop\ss\test-ancient-dna
   ```

2. **Activate Virtual Environment**:
   If not already set up, create and activate:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set Google API Key**:
   ```powershell
   echo GOOGLE_API_KEY=your-api-key > .env
   ```
   - Obtain the key:
     - Go to [Google Cloud Console](https://console.cloud.google.com/).
     - Create/select a project.
     - Navigate to **APIs & Services** > **Library**, enable "Gemini API".
     - Go to **Credentials**, click **Create Credentials** > **API Key**, and copy the key.

5. **Ensure Templates**:
   ```powershell
   mkdir templates
   echo "<html><body><h1>Ancient DNA Analysis API</h1></body></html>" > templates/index.html
   mkdir static
   ```

6. **Run the Server**:
   ```powershell
   python main.py
   ```
   - Output:
     ```
     INFO:     Started server process [...]
     INFO:     Uvicorn running on http://127.0.0.1:8000
     ```
   - Access the homepage at `http://localhost:8000` in a browser.

### On Render
1. **Push to GitHub**:
   ```powershell
   cd C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
   git add main.py utils.py requirements.txt templates static
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Configure Render**:
   - In Render dashboard, create a Web Service.
   - Link to `https://github.com/yourusername/ancient-dna-analysis`.
   - Set:
     - Runtime: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Environment Variable: `GOOGLE_API_KEY=your-api-key`

3. **Deploy**:
   - Trigger deployment in Render.
   - Access at `https://your-render-url.onrender.com`.

4. **Handle Cache Persistence**:
   - `sequence_cache.json` is ephemeral on Render.
   - After uploading a CSV (see below), commit `sequence_cache.json`:
     ```powershell
     cd C:\Users\hasin\OneDrive\Desktop\ss\test-ancient-dna
     copy sequence_cache.json C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
     cd C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
     git add sequence_cache.json
     git commit -m "Update sequence_cache.json"
     git push origin main
     ```
   - Redeploy to include `sequence_cache.json`.

## 2. Uploading Files

The `/upload-csv/` endpoint accepts CSV files to generate and cache DNA sequences.

### CSV Format
- Required columns: `id` (string), `region` (string), `age` (integer), `seed` (string, min 4 chars).
- Example (`sample.csv`):
  ```csv
  id,region,age,seed
  id_0010,emea,1000,agtc
  id_0011,emea,1000,agtc
  ```

### Steps
1. **Create a CSV**:
   ```powershell
   echo "id,region,age,seed" > sample.csv
   echo "id_0010,emea,1000,agtc" >> sample.csv
   echo "id_0011,emea,1000,agtc" >> sample.csv
   ```

2. **Upload Locally**:
   ```powershell
   curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
   ```
   - Response:
     ```json
     {"message": "Successfully uploaded and cached 2 records"}
     ```
   - Generates sequences (up to 5000 rows), caches them in `sequence_cache`, and saves to `sequence_cache.json`.

3. **Upload on Render**:
   ```powershell
   curl -X POST -F "file=@sample.csv" https://your-render-url.onrender.com/upload-csv/
   ```
   - Commit `sequence_cache.json` afterward (see above).

4. **Verify Cache**:
   ```powershell
   type sequence_cache.json
   ```
   - Example content:
     ```json
     {
       "id_0010": {"id": "id_0010", "region": "emea", "age": 1000, "seed": "agtc", "sequence": "agtcagtc..."},
       "id_0011": {"id": "id_0011", "region": "emea", "age": 1000, "seed": "agtc", "sequence": "agtcagtc..."}
     }
     ```
   - Check sequence length (max 5000):
     ```powershell
     type sequence_cache.json | jq '.id_0010.sequence | length'
     ```

## 3. Interacting with the API

The API provides five endpoints for DNA sequence analysis and querying.

### Endpoints

| Endpoint                  | Method | Description                              | Request Body/Parameters                  | Response Example                         |
|---------------------------|--------|------------------------------------------|------------------------------------------|------------------------------------------|
| `/`                       | GET    | Renders homepage (HTML)                 | -                                        | HTML page (`index.html`)                 |
| `/upload-csv/`            | POST   | Uploads CSV, generates/caches sequences | Form: `file` (CSV file)                  | `{"message": "Processed 2 records"}`     |
| `/generate-sequence/`     | POST   | Retrieves cached sequence by ID         | `{"id": "id_0010"}`                     | `{"id": "id_0010", "sequence": "agtc..."}` |
| `/compare-sequences/`     | POST   | Compares two sequences                  | `{"id1": "id_0010", "id2": "id_0011"}` | `{"id1": "id_0010", "id2": "id_0011", "similarity_score": 85.5}` |
| `/ask-me-anything/`       | POST   | Answers questions via Gemini LLM        | `{"question": "What does this API do?"}` | `{"answer": "This API analyzes..."}`     |

### Usage Examples

#### Homepage (`/`)
```powershell
curl http://localhost:8000/
```
- Response: HTML content from `templates/index.html`.
- Browser: Open `http://localhost:8000`.

#### Upload CSV (`/upload-csv/`)
```powershell
curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
```
- Response:
  ```json
  {"message": "Successfully uploaded and cached 2 records"}
  ```

#### Retrieve Sequence (`/generate-sequence/`)
```powershell
curl -X POST http://localhost:8000/generate-sequence/ -H "Content-Type: application/json" -d "{\"id\": \"id_0010\"}"
```
- Response (sequence truncated to 1000 chars):
  ```json
  {"id": "id_0010", "sequence": "agtcagtc..."}
  ```

#### Compare Sequences (`/compare-sequences/`)
```powershell
curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d "{\"id1\": \"id_0010\", \"id2\": \"id_0011\"}"
```
- Response:
  ```json
  {"id1": "id_0010", "id2": "id_0011", "similarity_score": 85.5}
  ```

#### Ask Questions (`/ask-me-anything/`)
```powershell
curl -X POST http://localhost:8000/ask-me-anything/ -H "Content-Type: application/json" -d "{\"question\": \"What does this API do?\"}"
```
- Response:
  ```json
  {"answer": "This API analyzes ancient DNA by generating sequences from CSV data, caching them, comparing sequences for similarity, and answering questions about its functionality."}
  ```

### Notes
- **Sequence Limits**: Sequences are capped at 5000 characters; `/generate-sequence/` returns the first 1000.
- **CSV Limits**: Processes up to 5000 rows per CSV.
- **Render**: Replace `http://localhost:8000` with `https://your-render-url.onrender.com` for deployed instances.

## Troubleshooting

### Running the Server
- **Error**: `ModuleNotFoundError` for dependencies.
  - **Fix**: Ensure `requirements.txt` is installed:
    ```powershell
    pip install -r requirements.txt
    ```
- **Error**: Server not starting (`port already in use`).
  - **Fix**: Kill existing process or change port:
    ```powershell
    python main.py --port 8001
    ```

### Uploading Files
- **Error**: `400 Bad Request` (invalid CSV).
  - **Fix**: Verify CSV has `id`, `region`, `age`, `seed` columns.
  - **Check**:
    ```powershell
    type sample.csv
    ```
- **Error**: Sequences not cached.
  - **Fix**: Check `sequence_cache.json`:
    ```powershell
    type sequence_cache.json
    ```

### Interacting with API
- **Error**: `404 Not Found` for sequence IDs.
  - **Fix**: Ensure IDs exist in `sequence_cache.json` after `/upload-csv/`.
- **Error**: `/ask-me-anything/` fails.
  - **Fix**: Verify `GOOGLE_API_KEY` in `.env` or Render environment.

## Additional Resources
- See [README.md](README.md) for project overview and setup.
- See [DOCUMENTATION.md](DOCUMENTATION.md) for architecture and maintenance details.
