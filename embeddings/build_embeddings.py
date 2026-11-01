"""
build_embeddings.py — Vector Cache Builder
============================================
Reads the structured menu CSV (redi_menu.csv) and generates
multilingual sentence embeddings for every item's `search_text` column.
The embeddings plus the DataFrame are serialized into a single pickle
file (menu_embeddings.pkl) that the search engine loads at runtime.

Usage:
    python build_embeddings.py
"""

import os
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── Configuration ────────────────────────────────────────────
CSV_PATH = "data_output/redi_menu.csv"
PKL_PATH = "embeddings/menu_embeddings.pkl"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def main():
    """Load menu data, encode search texts, and save the vector cache."""

    # 1. Load the structured dataset
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"{CSV_PATH} not found. Run the CSV generator script first."
        )

    df = pd.read_csv(CSV_PATH)
    print(f"[1/3] Dataset loaded - {len(df)} items from {CSV_PATH}")

    # 2. Encode search_text with a multilingual Sentence-BERT model
    print(f"[2/3] Loading model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    search_texts = df["search_text"].fillna("").tolist()
    embeddings = model.encode(search_texts, show_progress_bar=True, batch_size=32)
    print(f"      Embeddings shape: {embeddings.shape}")

    # 3. Bundle everything into a single pickle cache
    cache = {
        "dataframe": df,
        "embeddings": embeddings,
        "model_name": MODEL_NAME,
    }
    with open(PKL_PATH, "wb") as f:
        pickle.dump(cache, f)

    print(f"[3/3] Vector cache saved to {PKL_PATH}")


if __name__ == "__main__":
    main()
