"""Fixtures for testing the Hugging Face Classifier."""

import os

import datasets
import pandas as pd
import pytest

# --- Hugging Face Models to Test ---

# Full list of models for comprehensive testing
ALL_MODEL_NAMES = [
    "distilbert-base-uncased-finetuned-sst-2-english",
    "bert-base-uncased",
    "nlptown/bert-base-multilingual-uncased-sentiment",
    "unitary/toxic-bert",
    "lighteternal/fact-or-opinion-xlmr-el",
    "ayoubkirouane/BERT-Emotions-Classifier",
    "XSY/albert-base-v2-fakenews-discriminator",
    "s-nlp/xlmr_formality_classifier",
    "JonatanGk/roberta-base-bne-finetuned-hate-speech-offensive-spanish",
    "autopilot-ai/EthicalEye",
]

# Reduced list for faster CI runs (2 smallest models by size)
# XSY/albert-base-v2-fakenews-discriminator: 11.8M params, ~47 MB
# distilbert-base-uncased-finetuned-sst-2-english: 67M params, 268 MB
REDUCED_MODEL_NAMES = [
    "XSY/albert-base-v2-fakenews-discriminator",  # Smallest: ALBERT-base (11.8M params)
    "distilbert-base-uncased-finetuned-sst-2-english",  # Second smallest: DistilBERT (67M params)
]

# Check environment variable to determine which model list to use
# Set REDUCE_TEST_HF_MODELS=true in CI to use the reduced list
if os.environ.get("REDUCE_TEST_HF_MODELS", "").lower() in ("true", "1", "yes"):
    MODEL_NAMES = REDUCED_MODEL_NAMES
else:
    MODEL_NAMES = ALL_MODEL_NAMES


@pytest.fixture
def sample_dataset():
    """Creates a sample Hugging Face Dataset for testing."""
    data = {
        "id": [
            "sample_1",
            "sample_2",
            "sample_3",
        ],
        "text": [
            "This is a positive example.",
            "This is a negative one.",
            "A neutral statement.",
        ],
    }
    return datasets.Dataset.from_dict(data)


@pytest.fixture
def empty_dataset(tmpdir):
    """Create an empty parquet file."""
    empty_df = pd.DataFrame(columns=["id", "text"])
    file_path = os.path.join(tmpdir, "empty.parquet")
    empty_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def missing_columns_dataset(tmpdir):
    """Create a dataset with missing required columns."""
    test_df = pd.DataFrame(
        {
            "other_id": ["1", "2", "3"],
            "other_text": ["Sample text 1", "Sample text 2", "Sample text 3"],
        }
    )
    file_path = os.path.join(tmpdir, "missing_columns.parquet")
    test_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def problem_dataset(tmpdir):
    """Create a dataset with some problem records that would cause errors during processing."""
    test_df = pd.DataFrame(
        {
            "id": ["1", "2", "3", "4", "5"],
            "text": ["Valid text", "", 123, None, "Another valid text"],
        }
    )
    file_path = os.path.join(tmpdir, "problem_dataset.parquet")
    test_df.to_parquet(file_path)
    return file_path
