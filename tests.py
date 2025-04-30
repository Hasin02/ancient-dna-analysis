import pytest
from fastapi.testclient import TestClient
from main import app
import pandas as pd
import io

client = TestClient(app)

def test_upload_csv_valid():
    # Create a sample CSV
    csv_data = """id,region,age,seed
id_0010,emea,48,aagtaagtaagtaagtaagtaagtaagtaagtaagtaagtaagc"""
    csv_file = io.BytesIO(csv_data.encode('utf-8'))
    
    response = client.post(
        "/upload-csv/",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully uploaded 1 records"}

def test_upload_csv_invalid_columns():
    csv_data = """id,wrong_column,age,seed
id_0010,emea,48,aagtaagtaagtaagtaagtaagtaagtaagtaagtaagtaagc"""
    csv_file = io.BytesIO(csv_data.encode('utf-8'))
    
    response = client.post(
        "/upload-csv/",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )
    assert response.status_code == 400
    assert "missing required columns" in response.json()["detail"]

def test_generate_sequence_valid():
    # First upload data
    csv_data = """id,region,age,seed
id_0010,emea,48,aagtaagtaagtaagtaagtaagtaagtaagtaagtaagtaagc"""
    csv_file = io.BytesIO(csv_data.encode('utf-8'))
    client.post("/upload-csv/", files={"file": ("test.csv", csv_file, "text/csv")})
    
    response = client.post(
        "/generate-sequence/",
        json={"id": "id_0010"}
    )
    assert response.status_code == 200
    assert "sequence" in response.json()
    assert len(response.json()["sequence"]) <= 1000  # Truncated response

def test_generate_sequence_invalid_id():
    response = client.post(
        "/generate-sequence/",
        json={"id": "invalid_id"}
    )
    assert response.status_code == 404
    assert "Sample ID not found" in response.json()["detail"]

def test_compare_sequences_valid():
    csv_data = """id,region,age,seed
id_0010,emea,48,aagtaagtaagtaagtaagtaagtaagtaagtaagtaagtaagc
id_0011,emea,48,aagtaagtaagtaagtaagtaagtaagtaagtaagtaagtaagc"""
    csv_file = io.BytesIO(csv_data.encode('utf-8'))
    client.post("/upload-csv/", files={"file": ("test.csv", csv_file, "text/csv")})
    
    response = client.post(
        "/compare-sequences/",
        json={"id1": "id_0010", "id2": "id_0011"}
    )
    assert response.status_code == 200
    assert "similarity_score" in response.json()
    assert 0 <= response.json()["similarity_score"] <= 100

def test_ask_me_anything():
    response = client.post(
        "/ask-me-anything/",
        json={"question": "What does this API do?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()