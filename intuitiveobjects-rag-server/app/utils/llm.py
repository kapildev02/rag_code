# import ollama
# from typing import List, Dict, Any
# import json
# import logging
# import re
# import anyio  # if using async context

# logger = logging.getLogger(__name__)
# model_name = "qwen3:8b"


# def remove_think_tag(text: str) -> str:
#     """Remove <think>...</think> blocks from the text."""
#     return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


# async def expand_user_query(conversation: List[Dict[str, Any]], user_question: str) -> str:
#     """Expand user query using Ollama LLM with conversation context."""

#     # Ensure conversation is valid
#     if not isinstance(conversation, list):
#         conversation = [{"role": "user", "content": str(conversation)}]

#     if not conversation:
#         return user_question.strip()

#     system_prompt = {
#       "role": "system",
#      "content": (
#        """ You are an AI assistant that expands vague or ambiguous user queries into detailed, context-rich questions.

#             Return ONLY one expanded question in plain text.

#             If the user query is already a clear, well-formed question (starts with who, what, when, where, why, or how), keep it as-is unless it contains pronouns that must be resolved.

#             Use conversation history ONLY when the current query directly refers to something mentioned earlier (such as a person, document, or entity).

#             When the query contains pronouns like he, his, she, her, they, or it, resolve them ONLY if they clearly refer to an entity from the conversation history. Do not guess or hallucinate.

#             Do NOT use irrelevant context from previous messages.

#             Do NOT invent new entities.

#             Do NOT add explanations or reasoning.

#             Output ONLY the final expanded question.
# """

#     ),
# }
#     messages = [system_prompt] + conversation + [
#         {"role": "user", "content": f"Expand this query into a well-formed question: '{user_question}'"}
#     ]

#     print(f"[expand_user_query] Messages sent to Ollama: {messages}")

#     # Run ollama.chat in async-safe way

#     response = ollama.chat(
#         model=model_name,
#         messages=messages,
#         stream=False
#     )

#     print(f"[expand_user_query] Ollama raw response: {response}")

#     raw_content = (
#         response.get("message", {}).get("content") or
#         response.get("response") or
#         response.get("output") or
#         response.get("data", [{}])[0].get("content", "") or
#         ""
#     ).strip()

#     expanded_result = remove_think_tag(raw_content)
#     print(f"[expand_user_query] Expanded query: {expanded_result}")
#     return expanded_result

import ollama
from typing import List, Dict, Any
import json
import logging
import re
from app.db.mongodb import organization_user_collection, category_collection

# Add these imports:
from bson.objectid import ObjectId
from app.services.organization_admin_services import get_updated_app_config

logger = logging.getLogger(__name__)
model_name = "qwen3:8b"


def remove_think_tag(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


async def expand_user_query(conversation: List[Dict[str, Any]], user_question: str,user_id:str) -> str:
    """
    Expand user query using Ollama LLM with ONLY relevant conversation info,
    not the full message list.
    """
    existing_user = await organization_user_collection().find_one({"_id": ObjectId(user_id)})
    organization_id = existing_user.get("organization_id")
    config = await get_updated_app_config(organization_id)
    model_name = config.get("query_model", "qwen3:8b")
    print(f"model_name in expand_user_query: {model_name}")
    # Extract only the minimal useful context (names/entities)
    # NOT full messages
    context_text = ""
    for msg in conversation:
        if msg["role"] == "user":
            context_text += msg["content"] + "\n"
        elif msg["role"] == "assistant":
            context_text += msg["content"] + "\n"

    # Final clean context
    context_text = context_text.strip()

    system_prompt = {
        "role": "system",
        "content": """
You are an AI assistant that expands vague or ambiguous user queries into detailed, context-rich questions.

Return ONLY one expanded question in plain text.

If the user query is already a clear, well-formed question (starts with who, what, when, where, why, or how), keep it as-is unless it contains pronouns that must be resolved.

Use conversation history ONLY when the current query directly refers to something mentioned earlier (such as a person, document, or entity).

When the query contains pronouns like he, his, she, her, they, or it, resolve them ONLY if they clearly refer to an entity from the conversation history. Do not guess or hallucinate.

Do NOT use irrelevant context from previous messages.

Do NOT invent new entities.

Do NOT add explanations or reasoning.

Output ONLY the final expanded question.
""",
    }

    # Only minimal context + user query
    messages = [
        system_prompt,
        {"role": "user", "content": f"Conversation context:\n{context_text}"},
        {"role": "user", "content": f"Expand this query into a well-formed question: {user_question}"},
    ]

    print("[expand_user_query] Messages sent to Ollama:", messages)

    response = ollama.chat(
        model=model_name,
        messages=messages,
        stream=False
    )

    print("[expand_user_query] Ollama raw response:", response)

    raw_content = (
        response.get("message", {}).get("content", "") or
        response.get("response", "") or
        response.get("output", "")
    ).strip()

    expanded_result = remove_think_tag(raw_content)
    print("[expand_user_query] Expanded query:", expanded_result)

    return expanded_result
