import json
import os
import logging
import sys
import random

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
logger.handlers = [handler]
logger.setLevel(logging.INFO)

sequence_cache = {}

def load_cache():
    """Load sequence cache from file."""
    global sequence_cache
    cache_file = "sequence_cache.json"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                sequence_cache.update(json.load(f))
            logger.info(f"Loaded {len(sequence_cache)} sequences from {cache_file}")
    except Exception as e:
        logger.error(f"Error loading cache: {e}")

def save_cache():
    """Save sequence cache to file."""
    cache_file = "sequence_cache.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(sequence_cache, f)
        logger.info(f"Saved {len(sequence_cache)} sequences to {cache_file}")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def generate_dna_sequence(id_val, region, age, seed, max_len):
    """
    Generate a synthetic DNA sequence based on input parameters.
    Returns 'x' for invalid inputs.
    """
    try:
        if not id_val or not seed or not isinstance(age, int):
            logger.warning(f"Invalid input for ID {id_val}: seed={seed}, age={age}")
            return "x"
        # Simple sequence generation (replace with your actual logic)
        random.seed(seed)
        bases = ['A', 'C', 'G', 'T']
        sequence = ''.join(random.choice(bases) for _ in range(max_len))
        logger.info(f"Generated sequence length for ID {id_val}: {len(sequence)}")
        return sequence
    except Exception as e:
        logger.warning(f"Error generating sequence for ID {id_val}: {e}")
        return "x"

def calculate_similarity(seq1, seq2):
    """Calculate similarity score between two sequences."""
    try:
        if not seq1 or not seq2:
            return 0.0
        min_len = min(len(seq1), len(seq2))
        matches = sum(a == b for a, b in zip(seq1[:min_len], seq2[:min_len]))
        return (matches / min_len) * 100
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0
