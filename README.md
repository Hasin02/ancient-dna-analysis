Ancient DNA Analysis API
This is a FastAPI-based API for analyzing ancient DNA sequences. It allows users to upload CSV files containing sample data, generate DNA sequences, retrieve cached sequences, compare sequences for similarity, and ask questions about the API using a language model.
Features

Upload CSV: Process CSV files with sample data (id, region, age, seed) to generate and cache DNA sequences.
Generate Sequence: Retrieve a cached DNA sequence by sample ID.
Compare Sequences: Calculate a similarity score between two cached DNA sequences.
Ask Me Anything: Query the API’s functionality using natural language via Gemini LLM.
In-Memory Storage: Uses an in-memory cache (sequence_cache) with a JSON file (sequence_cache.json) for persistence.
Modular Codebase: Core logic split into main.py (API endpoints) and utils.py (utility functions).

Project Structure
├── main.py                 # FastAPI app and endpoints
├── utils.py               # Utility functions (sequence generation, similarity, cache management)
├── requirements.txt       # Python dependencies
├── sample.csv             # Sample CSV for testing
├── sequence_cache.json    # Cache file (generated at runtime)
├── templates/
│   └── index.html         # Homepage template
├── static/                # Static files (CSS, JS, etc.)
└── .github/
    └── workflows/
        └── test.yml       # GitHub Actions workflow

Prerequisites

Python 3.11+
Virtual environment (recommended)
Render account for deployment
Google API key for Gemini LLM (set as GOOGLE_API_KEY)

Setup
1. Clone the Repository
git clone https://github.com/yourusername/ancient-dna-analysis.git
cd ancient-dna-analysis

2. Create and Activate Virtual Environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Set Environment Variables
Create a .env file in the project root:
echo GOOGLE_API_KEY=your-google-api-key > .env

5. Verify Templates and Static Files
Ensure the templates/ and static/ directories exist:
mkdir templates static
echo "<html><body><h1>Ancient DNA Analysis API</h1></body></html>" > templates/index.html

Running Locally
python main.py


The API will run at http://localhost:8000.
Access the homepage in a browser: http://localhost:8000.

Usage
1. Upload CSV
Create a CSV file (e.g., sample.csv):
id,region,age,seed
id_0010,emea,1000,agtc
id_0011,emea,1000,agtc

Upload it:
curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/


Generates DNA sequences for up to 5000 rows and caches them in sequence_cache.
Saves cache to sequence_cache.json.

2. Retrieve Sequence
curl -X POST http://localhost:8000/generate-sequence/ -H "Content-Type: application/json" -d '{"id": "id_0010"}'


Returns the first 1000 characters of the cached sequence.

3. Compare Sequences
curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d '{"id1": "id_0010", "id2": "id_0011"}'


Returns a similarity score (0–100).

4. Ask Questions
curl -X POST http://localhost:8000/ask-me-anything/ -H "Content-Type: application/json" -d '{"question": "What does this API do?"}'


Answers using Gemini LLM.

Testing
Run unit tests with pytest:
pytest tests.py


Tests cover all endpoints using sample.csv.

GitHub Actions
The project uses GitHub Actions for CI/CD:

Workflow: .github/workflows/test.yml
Runs tests on push/pull requests to main.
Requires GOOGLE_API_KEY in repository secrets:
Go to Repository > Settings > Secrets and variables > Actions > New repository secret.
Name: GOOGLE_API_KEY, Value: your API key.



Deployment on Render

Push to GitHub:
git add .
git commit -m "Deploy to Render"
git push origin main


Create Render Web Service:

In Render dashboard, create a new Web Service.
Link to your GitHub repository (ancient-dna-analysis).
Set:
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Environment Variables: GOOGLE_API_KEY=your-google-api-key




Deploy:

Deploy the service.
Access at https://your-render-url.onrender.com.


Handle Cache Persistence:

Render’s filesystem is ephemeral, so sequence_cache.json is lost on restart.
After running /upload-csv/, download sequence_cache.json locally:cd test-ancient-dna
copy sequence_cache.json ../ancient-dna-analysis
cd ../ancient-dna-analysis
git add sequence_cache.json
git commit -m "Update sequence_cache.json"
git push origin main


Redeploy to include sequence_cache.json.
For persistent storage, consider Render’s PostgreSQL (see below).



Optional: Persistent Storage with PostgreSQL
To persist sequences across Render deployments:

Create a PostgreSQL database in Render.
Add DATABASE_URL to Render’s environment variables.
Update requirements.txt:echo psycopg2-binary==2.9.9 >> requirements.txt


Modify main.py to use PostgreSQL (contact maintainer for code).
Redeploy.

Troubleshooting

Local Issues:
Check sequence_cache.json:cat sequence_cache.json


Verify sequence length:type sequence_cache.json | jq '.id_0010.sequence | length'


Ensure templates/index.html exists.


Render Issues:
Check deployment logs in Render dashboard.
Verify GOOGLE_API_KEY is set.


GitHub Actions:
Check workflow logs in GitHub Actions tab.
Ensure GOOGLE_API_KEY is set in repository secrets.



Contributing

Fork the repository.
Create a feature branch: git checkout -b feature-name.
Commit changes: git commit -m "Add feature".
Push to branch: git push origin feature-name.
Open a pull request.

License
MIT License. See LICENSE for details.
Contact
For issues or suggestions, open an issue on GitHub or contact the maintainer.
