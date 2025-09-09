


import os
import json
import pickle
from pathlib import Path
from app.pipeline.keyword_search.bm25_engine import BM25
# from app.pipeline.keyword_search.text_utils import clean_and_tokenize

BM25_STORE = "app/pipeline/bm25_store"

def save_bm25_index(doc_id: str, processed_pages: list[str]):
    Path(BM25_STORE).mkdir(parents=True, exist_ok=True)

    # logger.info(f'chunks>>>>{chunks}')

    # tokenized_docs = [clean_and_tokenize(text) for text in chunks]
    # tokenized_docs = [clean_and_tokenize(chunk["text"]) for chunk in chunks]
    bm25 = BM25(processed_pages)
    bm25_path = os.path.join(BM25_STORE, f"{doc_id}.pkl")

    bm25.save_to_disk(bm25_path)

    # with open(os.path.join(BM25_STORE, f"{doc_id}_metadata.pkl"), "wb") as f:
    #     pickle.dump(metadata, f)

    with open(os.path.join(BM25_STORE, f"{doc_id}_texts.json"), "w") as f:
        json.dump(processed_pages, f)
