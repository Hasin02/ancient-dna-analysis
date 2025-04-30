**Ancient DNA Analysis API - Documentation**

**1. Overview**
The Ancient DNA Analysis API is a FastAPI-powered application designed for forensic research involving ancient remains. The API facilitates uploading ancient DNA datasets, generating long DNA sequences from input parameters, comparing genetic similarity between samples, and querying the system using natural language. It includes a user-friendly web interface and integrates Gemini's large language model for natural query support.

**2. Features**
- Upload CSV data containing sample information (id, region, age, seed)
- Generate a long DNA sequence for a given sample
- Compare DNA sequences between two samples
- Ask natural language questions regarding the API
- Frontend interface using Jinja2 and JavaScript
- Real-time loading indicators
- Fully tested using Pytest

**3. Installation**

**3.1 Clone the Repository**
```bash
git clone https://github.com/Hasin02/ancient-dna-analysis.git
cd ancient-dna-analysis
```

**3.2 Create Virtual Environment**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

**3.3 Install Dependencies**
```bash
pip install -r requirements.txt
```

**3.4 Environment Setup**
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key
```

**4. Run the Application**
```bash
python main.py
```
Access the frontend at: http://localhost:8000/
Access the API documentation at: http://localhost:8000/docs

**5. API Endpoints**

**POST /upload-csv/**
Uploads a CSV file containing ancient remains data.
- Required columns: id, region, age, seed

**POST /generate-sequence/**
Generates a DNA sequence based on a provided ID.
- Request body: `{ "id": "id_0010" }`

**POST /compare-sequences/**
Compares DNA sequences of two samples.
- Request body: `{ "id1": "id_0010", "id2": "id_0011" }`

**POST /ask-me-anything/**
Uses Gemini LLM to respond to natural language questions about the API.
- Request body: `{ "question": "What does this API do?" }`

**6. Sequence Generation Logic**
- Input: ID, region, age, and DNA seed
- Region determines a list of valid DNA motifs
- Motifs are extracted and randomly repeated using a seeded RNG
- Generates a long string (up to 1 billion characters)

**7. Sequence Comparison Logic**
- Sequences truncated to 5,000 characters
- 50% weight: Position-based similarity using difflib
- 50% weight: Motif overlap of 4-character subsequences

**8. Testing**
Test suite written using Pytest.
Run tests with:
```bash
pytest tests.py
```
Tests include:
- CSV upload validation
- Sequence generation
- Sequence comparison
- Ask-me-anything interaction

**9. Frontend Interface**
- Located in `templates/index.html` and `static/style.css`
- HTML forms for each API operation
- JavaScript provides real-time loading feedback and result display

**10. Deployment**

**Render Deployment (Recommended)**
- Connect GitHub repo to Render
- Set build command: `pip install -r requirements.txt && python main.py`
- Set environment variable: `GOOGLE_API_KEY`

**11. Requirements**
```
fastapi>=0.115.0
uvicorn>=0.30.6
pandas>=2.2.2
langchain-google-genai>=1.0.10
python-dotenv>=1.0.1
pytest>=8.3.3
langchain>=0.2.16
python-multipart>=0.0.12
jinja2>=3.1.2
```

**12. Repository**
GitHub: https://github.com/Hasin02/ancient-dna-analysis

