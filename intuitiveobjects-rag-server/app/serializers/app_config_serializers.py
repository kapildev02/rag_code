def AppConfigEntity(app_config) -> dict:
    return {
        "id": str(app_config["_id"]),
        "llm_model": app_config["llm_model"],
        "embedding_model": app_config["embedding_model"],
        "created_at": app_config["created_at"],
        "updated_at": app_config["updated_at"],
    }

def AppConfigListEntity(app_configs) -> list:
    return [AppConfigEntity(app_config) for app_config in app_configs]
