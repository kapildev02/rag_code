from .models import get_model_manager, llm_generate_response
from .rag_pipeline import similarity_search, enrich_query_context, hybrid_search, print_hybrid_search_results
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s')

# Add handler (console in this case)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

model_manager = get_model_manager()


def set_active_model(model_name):
    try:
        model_manager.set_active_model(model_name)
    except ValueError as e:
        logger.error(f"Failed to set active model: {str(e)}")
        raise

def initialize_models():
    try:
        model_manager.init_models()
        logger.info(f"Active model set to: {model_manager.active_model}")
    except ValueError as e:
        logger.error(f"Failed to initialize models: {str(e)}")
        raise
from app.services.app_config_service import get_app_configs
# async def process_query(query: str, tag: str="") -> list[dict]:
#     """
#     Process a user query through the RAG pipeline.
#     """
#     try:
#         app_config=await get_app_configs()
#         model_manager.set_active_model(app_config['llm_model'])  # Set the first model as active
#         temperature = app_config['temperature']  # Set the temperature for the model

#         search_results = similarity_search(query, tag=tag)
#         # hybrid_search_results = hybrid_search(query)
#         # print_hybrid_search_results(hybrid_search_results)

#         enriched_query = enrich_query_context(query, search_results)

#         # Generate response using the active model
#         active_model = model_manager.get_active_model()
#         # active_model = model_manager.initialize_qwen_model()
#         response = llm_generate_response(active_model, enriched_query, temperature=temperature)
#         #response = generate_response(enriched_query)
#         return response
#     except Exception as e:
#         logger.error(f"Error processing query: {str(e)}", exc_info=True)
#         return "I'm sorry, but I encountered an error while processing your query. Please try again later."

async def process_query(query: str, tag: str = "") -> list[dict]:
    try:
        app_config = await get_app_configs()
        model_manager.set_active_model(app_config['llm_model'])
        temperature = app_config['temperature']

        search_results = similarity_search(query_text=query, tag=tag)

        enriched_query = enrich_query_context(query, search_results)
        active_model = model_manager.get_active_model()

        response = llm_generate_response(active_model, enriched_query, temperature=temperature)
        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return [{
            "role": "assistant",
            "content": "I'm sorry, but I encountered an error while processing your query. Please try again later."
        }]
