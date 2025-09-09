def messageEntity(message) -> dict:
    return {
        "id": str(message["_id"]),
        "content": message["content"],
        "sources": message["sources"],
        "role": message["role"],
        "rating": message.get("rating", 0.0),
        "created_at": message["created_at"],
        "updated_at": message["updated_at"],
    }
# import json

# def messageEntity(message) -> dict:
#     content = message.get("content")
#     if isinstance(content, str):
#         try:
#             content = json.loads(content)
#         except json.JSONDecodeError:
#             pass
#     return {
#         "id": str(message["_id"]),
#         "content": content,
#         "role": message["role"],
#         "rating": message.get("rating", 0.0),
#         "created_at": message["created_at"],
#         "updated_at": message["updated_at"],
#     }


def messageListEntity(messages) -> list:
    return [messageEntity(message) for message in messages]
