from app.db.mongodb import app_config_collection
from app.schema.app_config_schema import CreateAppConfigRequest
from app.models.app_config_model import AppConfig
from app.serializers.app_config_serializers import AppConfigEntity, AppConfigListEntity

async def create_app_config(app_config: CreateAppConfigRequest):
    app_config = AppConfig(
        llm_model=app_config.llm_model,
        embedding_model=app_config.embedding_model,
    )
    result = await app_config_collection().insert_one(app_config.model_dump())
    app_config = await app_config_collection().find_one({"_id": result.inserted_id})
    return AppConfigEntity(app_config)


async def get_app_configs():
    app_configs = await app_config_collection().find().to_list()
    return AppConfigListEntity(app_configs)
