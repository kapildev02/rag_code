import ollama
from typing import List, Dict, Any
import json
import logging
import re
import anyio  # if using async context

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

    logger.info(f"[expand_user_query] Messages sent to Ollama: {messages}")

    # Run ollama.chat in async-safe way

    response = ollama.chat(
        model=model_name,
        messages=messages,
        stream=False
    )

    logger.info(f"[expand_user_query] Ollama raw response: {response}")

    raw_content = (
        response.get("message", {}).get("content") or
        response.get("response") or
        response.get("output") or
        response.get("data", [{}])[0].get("content", "") or
        ""
    ).strip()

    expanded_result = remove_think_tag(raw_content)
    logger.info(f"[expand_user_query] Expanded query: {expanded_result}")
    return expanded_result

