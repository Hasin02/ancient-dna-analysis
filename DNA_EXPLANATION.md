# DNA Sequence Generation and Comparison in Ancient DNA Analysis API

This document explains how the Ancient DNA Analysis API generates DNA sequences from input data and compares sequences to compute similarity scores. It is intended for users, developers, and researchers interested in understanding the core algorithms behind the `/upload-csv/`, `/generate-sequence/`, and `/compare-sequences/` endpoints.

## Overview

The API processes CSV files containing sample data (`id`, `region`, `age`, `seed`) to generate DNA sequences, which are cached in memory (`sequence_cache`) and persisted to `sequence_cache.json`. These sequences can be retrieved by ID or compared to calculate similarity scores. The generation and comparison logic is implemented in `utils.py`, ensuring modularity and maintainability.

### Key Processes
- **Sequence Generation**: Creates DNA sequences based on sample attributes and predefined motifs, using a deterministic random process.
- **Sequence Comparison**: Computes a similarity score (0–100) between two sequences using motif overlap and positional analysis.

## Sequence Generation

The `generate_dna_sequence` function in `utils.py` generates a DNA sequence for each sample in the uploaded CSV, called during the `/upload-csv/` endpoint.

### Input Parameters
- `id` (string): Unique sample identifier (e.g., `id_0010`).
- `region` (string): Geographic region (e.g., `emea`, `apac`, `na`, `latam`).
- `age` (integer): Sample age in years (e.g., 1000).
- `seed` (string): Seed sequence (min 4 characters, e.g., `agtc`).
- `max_cache_len` (integer): Maximum sequence length (default: 5000).

### Algorithm
1. **Input Validation**:
   - If `seed` is empty or < 4 characters, returns `"x"` (invalid sequence).
   - Example: `seed = "ag"` → `"x"`.

2. **Random Seed Initialization**:
   - Sets a deterministic random seed using `id`, `region`, and `age`:
     ```python
     random.seed(f"{id}+{region}+{age}")
     ```
   - Ensures consistent sequences for the same inputs.

3. **Motif Selection**:
   - Defines region-specific motifs (4-character DNA strings):
     ```python
     Q = {
         "apac": ["agtc", "agct", "actg", "atgc"],
         "na": ["gtac", "gcat", "gcta"],
         "latam": ["cgta", "ctga", "catg"],
         "emea": ["aagt", "aatg", "aagc"]
     }
     ```
   - Extracts 4-character substrings from `seed` that match any motif in `Q`:
     ```python
     motifs = [seed[i:i+4] for i in range(0, len(seed) - 3, 4) if seed[i:i+4] in {m for v in Q.values() for m in v}]
     ```
   - If no valid motifs, returns `"x"`.

4. **Sequence Construction**:
   - Builds the sequence by repeating randomly chosen motifs:
     - Select a motif from `motifs`.
     - Repeat it `n` times (`n` = random integer between 10 and 50).
     - Append to sequence until length approaches `max_cache_len` (5000).
     - Truncate to `max_cache_len` if exceeded.
   - Pseudocode:
     ```python
     sequence = []
     total_length = 0
     while total_length < max_cache_len:
         motif = random.choice(motifs)
         n = random.randint(10, 50)
         segment = motif * n
         if total_length + len(segment) > max_cache_len:
             segment = segment[:max_cache_len - total_length]
         sequence.append(segment)
         total_length += len(segment)
     return "".join(sequence)
     ```

5. **Storage**:
   - Stores the sequence in `sequence_cache[id]` with metadata (`id`, `region`, `age`, `seed`, `sequence`).
   - Saves `sequence_cache` to `sequence_cache.json` after processing all CSV rows.

### Example
- **Input**: `id="id_0010"`, `region="emea"`, `age=1000`, `seed="aagtaagc"`, `max_cache_len=5000`
- **Motifs**: From `seed`, valid motifs are `["aagt", "aagc"]` (matched with `Q["emea"]`).
- **Output**: Sequence like `aagtaagtaagt...aagcaagc...` (length ≤ 5000), stored in `sequence_cache["id_0010"]`.

### Verification
```powershell
cd C:\Users\hasin\OneDrive\Desktop\ss\test-ancient-dna
echo "id,region,age,seed" > sample.csv
echo "id_0010,emea,1000,aagtaagc" >> sample.csv
curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
type sequence_cache.json | jq '.id_0010.sequence | length'
```
- Expected: ≤ 5000 characters.

## Sequence Comparison

The `calculate_similarity` function in `utils.py` compares two sequences to compute a similarity score, called during the `/compare-sequences/` endpoint.

### Input Parameters
- `seq1` (string): First DNA sequence (from `sequence_cache[id1]`).
- `seq2` (string): Second DNA sequence (from `sequence_cache[id2]`).

### Algorithm
1. **Input Validation**:
   - If either sequence is empty, `"x"`, or missing, returns `0.0`.
   - If `seq1 == seq2`, returns `100.0`.

2. **Sequence Truncation**:
   - Limits both sequences to 5000 characters to manage performance:
     ```python
     s1, s2 = seq1[:5000], seq2[:5000]
     ```

3. **Positional Similarity (50%)**:
   - Uses `difflib.SequenceMatcher` to compute a ratio of matching positions:
     ```python
     pos_score = difflib.SequenceMatcher(None, s1, s2).ratio() * 50
     ```
   - Scales to contribute up to 50% of the total score.

4. **Motif Similarity (50%)**:
   - Extracts all 4-character substrings (motifs) from both sequences:
     ```python
     m1 = {s1[i:i+4] for i in range(len(s1) - 3)}
     m2 = {s2[i:i+4] for i in range(len(s2) - 3)}
     ```
   - Computes the Jaccard similarity of motif sets:
     ```python
     common = m1 & m2
     motif_score = (len(common) / max(len(m1), len(m2))) * 50 if m1 and m2 else 0.0
     ```
   - Scales to contribute up to 50% of the total score.

5. **Total Score**:
   - Combines scores and rounds to 2 decimal places:
     ```python
     return round(pos_score + motif_score, 2)
     ```

### Example
- **Input**:
  - `seq1 = "aagtaagtaagt..."` (length ≤ 5000)
  - `seq2 = "aagcaagcaagc..."` (length ≤ 5000)
- **Positional Similarity**: `difflib` finds partial matches (e.g., 60% match → `0.6 * 50 = 30`).
- **Motif Similarity**: Common 4-mers (e.g., `{"aagt", "aagc"}`) yield a Jaccard score (e.g., `0.8 * 50 = 40`).
- **Output**: `30 + 40 = 70.0` (score: 70.0).

### Verification
```powershell
curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d "{\"id1\": \"id_0010\", \"id2\": \"id_0011\"}"
```
- Response:
  ```json
  {"id1": "id_0010", "id2": "id_0011", "similarity_score": 85.5}
  ```

## Storage and Usage

### Storage
- **In-Memory**: Sequences are stored in `sequence_cache` (dictionary) during runtime.
- **Persistent**: `sequence_cache` is saved to `sequence_cache.json` after each `/upload-csv/`.
- **Format**:
  ```json
  {
    "id_0010": {
      "id": "id_0010",
      "region": "emea",
      "age": 1000,
      "seed": "aagtaagc",
      "sequence": "aagtaagtaagt..."
    }
  }
  ```

### CSV Input
- Uploaded via `/upload-csv/`:
  ```powershell
  curl -X POST -F "file=@sample.csv" http://localhost:8000/upload-csv/
  ```
- Triggers `generate_dna_sequence` for each row.

### Retrieval
- Use `/generate-sequence/` to fetch sequences:
  ```powershell
  curl -X POST http://localhost:8000/generate-sequence/ -H "Content-Type: application/json" -d "{\"id\": \"id_0010\"}"
  ```

### Comparison
- Use `/compare-sequences/` to compare:
  ```powershell
  curl -X POST http://localhost:8000/compare-sequences/ -H "Content-Type: application/json" -d "{\"id1\": \"id_0010\", \"id2\": \"id_0011\"}"
  ```

## Notes
- **Deterministic Generation**: Same `id`, `region`, `age` produce identical sequences due to `random.seed`.
- **Performance**: Sequences and comparisons are capped at 5000 characters to optimize memory and speed.
- **Render Deployment**: `sequence_cache.json` is ephemeral; commit to GitHub for persistence:
  ```powershell
  cd C:\Users\hasin\OneDrive\Desktop\ss\test-ancient-dna
  copy sequence_cache.json C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
  cd C:\Users\hasin\OneDrive\Desktop\ancient-dna-analysis
  git add sequence_cache.json
  git commit -m "Update sequence_cache.json"
  git push origin main
  ```

## Additional Resources
- [HOWTO.md](HOWTO.md): Running the server, uploading files, and interacting with the API.
- [DOCUMENTATION.md](DOCUMENTATION.md): Project architecture and setup.
- [README.md](README.md): Project overview.
