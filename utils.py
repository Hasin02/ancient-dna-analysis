import random as R
import json
import os
import logging
import difflib

# Set up logging
logger = logging.getLogger(__name__)

# In-memory sequence cache
sequence_cache = {}

# Cache file
CACHE_FILE = "sequence_cache.json"

def load_cache():
    """Load sequence cache from JSON file if it exists."""
    global sequence_cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                sequence_cache = json.load(f)
            logger.info(f"Loaded {len(sequence_cache)} sequences from {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Error loading cache: {e}")

def save_cache():
    """Save sequence cache to JSON file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(sequence_cache, f)
        logger.info(f"Saved {len(sequence_cache)} sequences to {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def generate_dna_sequence(id: str, region: str, age: int, dna_seed: str, max_cache_len: int = 5000) -> str:
    """Generate a DNA sequence based on sample ID, region, age, and seed."""
    try:
        if not dna_seed or len(dna_seed) < 4:
            logger.warning(f"Invalid seed for ID {id}")
            return "x"
        R.seed(f"{id}+{region}+{age}")
        Q = {
            "apac": ["agtc", "agct", "actg", "atgc"],
            "na": ["gtac", "gcat", "gcta"],
            "latam": ["cgta", "ctga", "catg"],
            "emea": ["aagt", "aatg", "aagc"],
        }
        motifs = [
            dna_seed[i:i+4]
            for i in range(0, len(dna_seed) - 3, 4)
            if dna_seed[i:i+4] in {m for v in Q.values() for m in v}
        ]
        if not motifs:
            logger.warning(f"No valid motifs for ID {id}")
            return "x"
        L, total, max_len = [], 0, max_cache_len
        while total < max_len:
            z = R.choice(motifs)
            n = R.randint(10, 50)
            w = z * n
            if total + len(w) > max_len:
                w = w[:max_len - total]
            L.append(w)
            total += len(w)
        seq = "".join(L)
        logger.info(f"Generated sequence length for ID {id}: {len(seq)}")
        if len(seq) > max_cache_len:
            logger.warning(f"Sequence too long for ID {id}: {len(seq)}")
            seq = seq[:max_cache_len]
        return seq
    except Exception as e:
        logger.error(f"Error in generate_dna_sequence for ID {id}: {e}")
        return "x"

def calculate_similarity(seq1: str, seq2: str) -> float:
    """Calculate similarity score between two DNA sequences."""
    if not seq1 or not seq2 or seq1 == "x" or seq2 == "x":
        return 0.0
    if seq1 == seq2:
        return 100.0
    s1, s2 = seq1[:5000], seq2[:5000]
    pos_score = difflib.SequenceMatcher(None, s1, s2).ratio() * 50
    m1 = {s1[i:i+4] for i in range(len(s1) - 3)}
    m2 = {s2[i:i+4] for i in range(len(s2) - 3)}
    common = m1 & m2
    motif_score = (len(common) / max(len(m1), len(m2))) * 50 if m1 and m2 else 0.0
    return round(pos_score + motif_score, 2)
