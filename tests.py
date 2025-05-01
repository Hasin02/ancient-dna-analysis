import pytest
import os
import logging
import sys
from fastapi.testclient import TestClient
from main import app
import utils
import pandas as pd
from unittest.mock import MagicMock, patch
from io import BytesIO

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
logger.handlers = [handler]
logger.setLevel(logging.INFO)

# Initialize TestClient
client = TestClient(app)

# Fixture to create a sample CSV
@pytest.fixture
def sample_csv(tmp_path):
    data = {
        "id": ["id_0010", "id_0011"],
        "region": ["emea", "emea"],
        "age": [1000, 1000],
        "seed": ["aagtaagc", "aagtaagc"]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

# Fixture to clear sequence_cache
@pytest.fixture(autouse=True)
def clear_cache():
    logger.info(f"Clearing sequence_cache: {len(utils.sequence_cache)} sequences")
    utils.sequence_cache.clear()
    yield
    utils.sequence_cache.clear()
    logger.info("Cleared sequence_cache after test")

# Test homepage
def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ancient DNA Analysis Interface" in response.text

# Test CSV upload
def test_upload_csv_endpoint(sample_csv):
    with open(sample_csv, "rb") as f:
        response = client.post("/upload-csv/", files={"file": ("sample.csv", f, "text/csv")})
    assert response.status_code == 200
    assert "Successfully uploaded and cached 2 records" in response.json()["message"]
    logger.info(f"sequence_cache after upload: {list(utils.sequence_cache.keys())}")
    assert "id_0010" in utils.sequence_cache
    assert "id_0011" in utils.sequence_cache
    assert len(utils.sequence_cache["id_0010"]["sequence"]) <= 5000
    assert utils.sequence_cache["id_0010"]["sequence"] != "x"

# Test sequence generation
def test_generate_sequence_endpoint(sample_csv):
    with open(sample_csv, "rb") as f:
        client.post("/upload-csv/", files={"file": ("sample.csv", f, "text/csv")})
    response = client.post("/generate-sequence/", json={"id": "id_0010"})
    assert response.status_code == 200
    assert response.json()["id"] == "id_0010"
    assert len(response.json()["sequence"]) <= 1000  # Truncated response

# Test sequence comparison
def test_compare_sequences_endpoint(sample_csv):
    with open(sample_csv, "rb") as f:
        client.post("/upload-csv/", files={"file": ("sample.csv", f, "text/csv")})
    response = client.post("/compare-sequences/", json={"id1": "id_0010", "id2": "id_0011"})
    assert response.status_code == 200
    assert response.json()["id1"] == "id_0010"
    assert response.json()["id2"] == "id_0011"
    assert 0 <= response.json()["similarity_score"] <= 100

# Test ask-me-anything (mock Gemini LLM and PromptTemplate)
@patch("main.PromptTemplate")
@patch("main.ChatGoogleGenerativeAI")
def test_ask_me_anything_endpoint(mock_llm, mock_prompt):
    logger.info("Setting up mocks for ChatGoogleGenerativeAI and PromptTemplate")
    # Mock PromptTemplate
    mock_prompt_instance = MagicMock()
    mock_prompt.return_value = mock_prompt_instance
    # Mock ChatGoogleGenerativeAI
    mock_llm_instance = MagicMock()
    mock_llm.return_value = mock_llm_instance
    mock_llm_instance.invoke.return_value.content = "This API analyzes DNA sequences."
    # Mock the chain (prompt | llm)
    mock_chain = MagicMock()
    mock_prompt_instance.__or__.return_value = mock_chain
    mock_chain.invoke.return_value.content = "This API analyzes DNA sequences."
    response = client.post("/ask-me-anything/", json={"question": "What does this API do?"})
    logger.info(f"Response status: {response.status_code}, body: {response.json()}")
    assert response.status_code == 200
    assert "answer" in response.json(), f"Response missing 'answer' key: {response.json()}"
    assert "This API analyzes DNA sequences" in response.json()["answer"]
    logger.info(f"Response answer: {response.json()['answer']}")

# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])
