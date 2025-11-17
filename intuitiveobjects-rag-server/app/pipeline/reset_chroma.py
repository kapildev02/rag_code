import chromadb
from chromadb.utils import embedding_functions
import logging
import os
import shutil

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_chroma_collection():
    try:
        PERSIST_DIRECTORY = "chromadb_storage"
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)

        chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        if "rag-chroma" in [c.name for c in chroma_client.list_collections()]:
            logger.info("Existing collection found. Deleting it...")
            chroma_client.delete_collection("rag-chroma")
            logger.info("Collection deleted.")

        # Optionally re-init client to avoid cache issues
        chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

        new_collection = chroma_client.create_collection(
            name="rag-chroma",
            embedding_function=embedding_function
        )
        logger.info("New collection created successfully.")

        # --- NEW: reset BM25 store ---
        BM25_DIR = "app/pipeline/bm25_store"
        try:
            if os.path.isdir(BM25_DIR):
                logger.info(f"Removing existing BM25 store at: {BM25_DIR}")
                shutil.rmtree(BM25_DIR)
            os.makedirs(BM25_DIR, exist_ok=True)
            logger.info(f"BM25 store reset at: {BM25_DIR}")
        except Exception as e:
            logger.error(f"Failed to reset BM25 store: {e}")
            # continue — Chroma already reset; return False to indicate partial failure
            return False

        #--- NEW: output_md_files ---
        output_md = "output_md_files"
        try : 
            if os.path.isdir(output_md):
                logger.info(f"Removing existing output_md_files at: {output_md}")
                shutil.rmtree(output_md)
            os.makedirs(output_md, exist_ok=True)
            logger.info(f"output_md_files reset at: {output_md}")

        except Exception as e:
            logger.error(f"Failed to reset output_md_files: {e}")
            return False
        
        #--- NEW: splited_pdf_files ---
        splited_pdf = "splited_pdf_pages"
        try : 
            if os.path.isdir(splited_pdf):
                logger.info(f"Removing existing splited_pdf_files at: {splited_pdf}")
                shutil.rmtree(splited_pdf)
            os.makedirs(splited_pdf, exist_ok=True)
            logger.info(f"splited_pdf_files reset at: {splited_pdf}")

        except Exception as e:
            logger.error(f"Failed to reset splited_pdf_files: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"An error occurred while resetting the ChromaDB collection: {str(e)}")
        return False

if __name__ == "__main__":
    if reset_chroma_collection():
        logger.info("ChromaDB collection and BM25 store reset completed successfully.")
    else:
        logger.error("Failed to reset ChromaDB collection and/or BM25 store.")
