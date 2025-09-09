import ollama
from typing import List, Dict, Any
import json
import logging
import re
import anyio  # if using async context
from keybert import KeyBERT
import spacy 


logger = logging.getLogger(__name__)
model_name = "qwen3:8b"


def remove_think_tag(text: str) -> str:
    """Remove <think>...</think> blocks from the text."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


async def expand_user_query(conversation: List[Dict[str, Any]], user_question: str) -> str:
    """Expand user query using Ollama LLM with conversation context."""

    # Ensure conversation is valid
    if not isinstance(conversation, list):
        conversation = [{"role": "user", "content": str(conversation)}]

    if not conversation:
        return user_question.strip()

    system_prompt = {
        "role": "system",
        "content": (
                "You are an AI assistant that expands vague or ambiguous user queries into detailed, context-rich questions.\n"
                "If the user query is already a clear, well-formed question (e.g., starts with 'who', 'what', 'when', 'where', 'why', or 'how'), KEEP it as-is and do not transform it into a yes/no question.\n"
                "You MUST use all relevant information from the conversation history, including project names, entities, or details mentioned in previous user queries and assistant responses.\n"
                "If the conversation history contains the answer to an ambiguous part of the current query (such as a project name), use it to make the expanded question specific and complete.\n"
                "NEVER ask the user for more context if it is already present in the conversation history.\n"
                "NEVER repeat or rephrase the user's request for clarification if you can resolve it from context.\n"
                "ONLY use information present in the conversation history or the current query.\n"
                "DO NOT assume or hallucinate names, entities, or facts that are not explicitly mentioned.\n"
                "Return a single, well-formed natural language question that is as specific as possible using all available context.\n"
                "DO NOT explain or generate paragraphs."
            ),
    }

    messages = [system_prompt] + conversation + [
        {"role": "user", "content": f"Expand this query into a well-formed question: '{user_question}'"}
    ]

    print(f"[expand_user_query] Messages sent to Ollama: {messages}")

    # Run ollama.chat in async-safe way

    response = ollama.chat(
        model=model_name,
        messages=messages,
        stream=False
    )

    print(f"[expand_user_query] Ollama raw response: {response}")

    raw_content = (
        response.get("message", {}).get("content") or
        response.get("response") or
        response.get("output") or
        response.get("data", [{}])[0].get("content", "") or
        ""
    ).strip()

    expanded_result = remove_think_tag(raw_content)
    print(f"[expand_user_query] Expanded query: {expanded_result}")
    return expanded_result




nlp = spacy.load("en_core_web_sm")

class KeywordExtractor:
    def __init__(self):
        self.kw_model = KeyBERT()
        self.stopwords = spacy.lang.en.stop_words.STOP_WORDS

    def preprocess(self, query: str):
        """Tokenize, remove stopwords/punct, lemmatize"""
        doc = nlp(query.lower())

        # First try to keep only nouns/proper nouns
        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct and token.pos_ in {"NOUN", "PROPN"}
        ]

        # Fallback: if nothing extracted, keep all alphabetic words
        if not tokens:
            tokens = [
                token.lemma_
                for token in doc
                if not token.is_stop and not token.is_punct and token.is_alpha
            ]

        return tokens

    def extract_phrases(self, query: str):
        """Extract multi-word noun phrases"""
        doc = nlp(query)
        phrases = [
            chunk.text.lower()
            for chunk in doc.noun_chunks
            if len(chunk.text.split()) > 1
        ]
        return phrases

    def extract_keywords(self, query: str, top_n: int = 10):
        """Rank keywords with KeyBERT; fallback to raw candidates if empty"""
        candidates = list(dict.fromkeys(self.preprocess(query) + self.extract_phrases(query)))

        if not candidates:
            return []

        ranked = self.kw_model.extract_keywords(
            query,
            candidates=candidates,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=top_n,
        )

        if ranked:
            return [kw for kw, score in ranked]
        else:
            return candidates[:top_n]




# import ast

# def filter_chunks_by_keywords(chunks, keywords):
#     """
#     Filter chunks based on keywords present in file_metadata or content.
#     Args:
#         chunks: List of Document objects
#         keywords: List of keywords to search for (case-insensitive)
#     Returns:
#         List of matching chunks
#     """
#     matched_chunks = []

#     for doc in chunks:
#         meta_match = False
#         content_match = False

#         # 1️⃣ Check file_metadata
#         file_meta_str = doc.metadata.get("file_metadata", "")
#         if file_meta_str:
#             try:
#                 file_meta = ast.literal_eval(file_meta_str)
#             except Exception:
#                 file_meta = {}
            
#             # Check if any keyword is in the file_metadata values
#             for val in file_meta.values():
#                 if any(k.lower() in str(val).lower() for k in keywords):
#                     meta_match = True
#                     break

#         # 2️⃣ Check content if not matched in metadata
#         if not meta_match:
#             content_text = doc.page_content or ""
#             if any(k.lower() in content_text.lower() for k in keywords):
#                 content_match = True

#         # 3️⃣ Include chunk if match found
#         if meta_match or content_match:
#             matched_chunks.append(doc)

#     return matched_chunks

# # --- Example usage ---
# keywords = ['stipend', 'vishwa']  # your query keywords
# filtered_chunks = filter_chunks_by_keywords(retrieved_docs, keywords)

# # Print filtered chunks
# for i, doc in enumerate(filtered_chunks, start=1):
#     print(f"\n--- Matched Chunk {i} ---")
#     print("ID:", doc.id)
#     print("Metadata:", doc.metadata)
#     print("Content:\n", doc.page_content)
