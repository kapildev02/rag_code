import os
import json
from pathlib import Path
from typing import List
from app.pipeline.keyword_search.bm25_engine import BM25


class KeywordSearchManager:
    def __init__(self, store_path: str = "app/pipeline/bm25_store"):
        self.store_path = store_path
        Path(self.store_path).mkdir(parents=True, exist_ok=True)

    def save_index(self, doc_id: str, tokenized_pages: List[List[str]]):
        """
        Save BM25 index and texts for a document.
        """
        bm25 = BM25(tokenized_pages)

        # Save BM25 model
        bm25_path = os.path.join(self.store_path, f"{doc_id}.pkl")
        bm25.save_to_disk(bm25_path)

        # Save tokenized texts
        text_path = os.path.join(self.store_path, f"{doc_id}_texts.json")
        with open(text_path, "w", encoding="utf-8") as f:
            json.dump(tokenized_pages, f, ensure_ascii=False, indent=2)

        print(f"[BM25] Index saved → {bm25_path}")
        print(f"[BM25] Texts saved → {text_path}")

    def load_index(self, doc_id: str) -> BM25:
        """
        Load BM25 index for a given document.
        """
        bm25_path = os.path.join(self.store_path, f"{doc_id}.pkl")
        if not os.path.exists(bm25_path):
            raise FileNotFoundError(f"No BM25 index found for doc_id={doc_id}")
        return BM25.load_from_disk(bm25_path)

    def search(self, doc_id: str, query: str, top_n: int = 5):
        """
        Perform a BM25 search on a specific document.
        """
        bm25 = self.load_index(doc_id)
        query_tokens = query.split()  # simple tokenization
        results = bm25.get_top_n(query_tokens, n=top_n)

        # Load texts for context
        text_path = os.path.join(self.store_path, f"{doc_id}_texts.json")
        with open(text_path, "r", encoding="utf-8") as f:
            tokenized_pages = json.load(f)

        ranked_results = [
            {"rank": i + 1, "score": score, "text": " ".join(tokenized_pages[idx])}
            for i, (idx, score) in enumerate(results)
        ]
        return ranked_results
