# import os
# import pymongo
# import logging

# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from pymongo import MongoClient  # Ensure you import MongoClient
# from gridfs import GridFS
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from bson import ObjectId
# from .document_processor import process_document
# from .chroma_db import chroma_add_chunks
# from .bm25.bm25_impl import BM25Index

# from .logger_config import setup_logger
# from .models import get_model_manager,llm_generate_response
# from app.pipeline.file_processors.extaract_metadata import generate_document_metadata
# from app.pipeline.progress_tracker import set_progress

# # Set up logging
# logger = setup_logger(__name__, log_level=logging.DEBUG)
# #generate_document_metadata
# # Set up MongoDB connection
# mongo_client = MongoClient("mongodb://localhost:27017/rag_ui")
# db = mongo_client["database_name"]
# fs = GridFS(db)

# model_manager = get_model_manager()

# bm25_index = BM25Index("./bm25_index_store", True)

# def get_gridfs():
#     """Create a new GridFS instance for thread-safe access."""
#     return fs

# # def chunk_document(document, chunk_size=1000):
# #     """
# #     Chunk a document into smaller pieces.
    
# #     Args:
# #         document (str): The document to be chunked.
# #         chunk_size (int): The maximum length of each chunk.
    
# #     Returns:
# #         List[str]: A list of chunked documents.
# #     """

    
# #     text_splitter = RecursiveCharacterTextSplitter(
# #         chunk_size=chunk_size,
# #         chunk_overlap=200,
# #         length_function=len,
# #         separators=["\n\n", "\n", " ", "", "."]
# #     )
# #     chunks = text_splitter.split_text(document)
# #     logger.info(f"Document chunked into {len(chunks)} pieces")
# #     for i, chunk in enumerate(chunks):
# #         logger.info(f"-----Chunk num {i} ----")
# #         logger.info({chunk})
# #         logger.info("\n\n")
# #     return chunks



# # def chunk_document(pages: list[str], metadata_results: list[dict], chunk_size=300, overlap=50) -> list[dict]:
# #     """
# #     Chunks page texts and includes metadata from metadata_results.
    
# #     Returns:
# #         A list of dicts with: chunk_id, text, page, metadata
# #     """
# #     # Create a quick lookup: { page_number: metadata_dict }
# #     metadata_map = {m["page"]: m["metadata"] for m in metadata_results}

# #     all_chunks = []

# #     for page_num, page_text in enumerate(pages, 1):
# #         page_metadata = metadata_map.get(page_num, {})  # fallback to empty dict
# #         start = 0

# #         while start < len(page_text):
# #             end = start + chunk_size
# #             chunk = page_text[start:end]

# #             chunk_id = f"page{page_num}_chunk{start}"

# #             all_chunks.append({
# #                 "chunk_id": chunk_id,
# #                 "text": chunk,
# #                 "page": page_num,
# #                 "metadata": page_metadata
# #             })

# #             start += chunk_size - overlap

# #     return all_chunks


# # def chunk_document(pages: list[str], metadata: dict, chunk_size=500, overlap=100) -> list[dict]:
# #     """
# #     Chunks page texts and includes a single metadata dictionary for the entire document.

# #     Returns:
# #         A list of dicts with: chunk_id, text, page, metadata
# #     """
# #     all_chunks = []

# #     for page_num, page_text in enumerate(pages, 1):
# #         start = 0

# #         while start < len(page_text):
# #             end = start + chunk_size
# #             chunk = page_text[start:end]
# #             chunk_id = f"page{page_num}_chunk{start}"

# #             all_chunks.append({
# #                 "chunk_id": chunk_id,
# #                 "text": chunk,
# #                 "page": page_num,
# #                 "metadata": metadata  # same metadata for all chunks
# #             })

# #             start += chunk_size - overlap

# #     return all_chunks




# def chunk_document(pages: list[str], metadata: dict, chunk_size=500, overlap=100) -> list[dict]:
#     """
#     Chunk the full document (combined pages) into meaningful pieces using LangChain splitter.
#     Includes document-level metadata with each chunk.
#     Returns:
#         A list of dicts with: chunk_id, text, page=None (not tracked per page), metadata
#     """
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=overlap,
#         length_function=len,
#         separators=["\n\n", "\n", " ", "", "."]
#     )
#     full_text = "\n".join(pages).strip()
#     chunks = text_splitter.split_text(full_text)
#     logger.info(f"Document chunked into {len(chunks)} pieces")
#     chunked_with_metadata = []
#     for i, chunk in enumerate(chunks):
#         chunk_id = f"chunk_{i}"
#         chunked_with_metadata.append({
#             "chunk_id": chunk_id,
#             "text": chunk,
#             "metadata": metadata
#         })
#         logger.debug(f"Chunk {i}: {chunk[:100]}...")
#     return chunked_with_metadata




# # def process_uploaded_document(file_id_str):
# #     """
# #     Process an uploaded document: retrieve from MongoDB, chunk it,
# #     generate embeddings, and store in ChromaDB.

# #     Args:
# #         file_id_str: String form of the ID of the file in MongoDB GridFS.
# #     """
# #     try:
# #         file_id = ObjectId(file_id_str)
# #         logger.info(f"Starting to process document with ID {file_id}")

# #         fs = get_gridfs() 
# #         # print('fs>>>>>>>' , fs)

# #         if not fs.exists(file_id):
# #             logger.error(f"File with ID {file_id} does not exist in GridFS")
# #             return

# #         grid_file = fs.get(file_id)
# #         # print('grid file >>>>>' , grid_file)
# #         file_content = grid_file.read()
# #         # print('file content >>>>>' , file_content)

# #         logger.info(f"Retrieved document from MongoDB, size: {len(file_content)} bytes")

# #         page_texts  = process_document(file_content)  

# #         model_name = model_manager.initialize_gemma_model() 
        
# #         metadata = generate_document_metadata(page_texts,model_name) 



        
# #         if page_texts is None:
# #             logger.warning("No text extracted from document")
# #             return

# #         # chunks = chunk_document(text) 

# #         chunks = chunk_document(page_texts, metadata)



# #         # logger.info(f"Document chunked into {len(chunks)} pieces")

# #         chroma_add_chunks(chunks, file_id)
# #         # bm25_index.add_document_chunks(chunks, file_id)

# #         logger.info(f"Completed processing document with ID {file_id}")
# #         return True

# #     except Exception as e:
# #         logger.error(f"Error processing document with ID {file_id}: {e}")
# #         logger.exception("Full traceback:")


# def process_uploaded_document(file_id_str):
#     """
#     Process an uploaded document: retrieve from MongoDB, chunk it,
#     generate embeddings, and store in ChromaDB.
#     Args:
#         file_id_str: String form of the ID of the file in MongoDB GridFS.
#     """
#     try:
#         file_id = ObjectId(file_id_str)
#         logger.info(f"Starting to process document with ID {file_id}")
#         fs = get_gridfs()
#         # print('fs>>>>>>>' , fs)
#         if not fs.exists(file_id):
#             logger.error(f"File with ID {file_id} does not exist in GridFS")
#             return
#         grid_file = fs.get(file_id)
#         # print('grid file >>>>>' , grid_file)
#         file_content = grid_file.read()
#         # print('file content >>>>>' , file_content)
#         # progress_map[file_id_str] = 20
#         logger.info(f"Retrieved document from MongoDB, size: {len(file_content)} bytes")
#         page_texts  = process_document(file_content)
#         # progress_map[file_id_str] = 40
#         set_progress(file_id_str, 20)
#         model_name = model_manager.initialize_gemma_model()
#         set_progress(file_id_str, 40)
#         metadata = generate_document_metadata(page_texts,model_name)
#         set_progress(file_id_str, 60)
#         if page_texts is None:
#             logger.warning("No text extracted from document")
#             return
#         # chunks = chunk_document(text)
#         chunks = chunk_document(page_texts, metadata)
#         # progress_map[file_id_str] = 70
#         set_progress(file_id_str, 80)
        
#         chroma_add_chunks(chunks, file_id)
#         # bm25_index.add_document_chunks(chunks, file_id)
#         # progress_map[file_id_str] = 100
#         set_progress(file_id_str, 100)
#         logger.info(f"Completed processing document with ID {file_id}")
#         return True
#     except Exception as e:
#         logger.error(f"Error processing document with ID {file_id}: {e}")
#         logger.exception("Full traceback:")
#         set_progress(file_id_str, -1)



import os
import pymongo
import logging
import zipfile
import threading
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymongo import MongoClient  # Ensure you import MongoClient
from gridfs import GridFS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bson import ObjectId
from .document_processor import process_document
from .chroma_db import chroma_add_chunks
from .bm25.bm25_impl import BM25Index

from .logger_config import setup_logger
from .models import get_model_manager,llm_generate_response
from app.pipeline.file_processors.extaract_metadata import generate_document_metadata
from app.pipeline.progress_tracker import progress_map


from app.pipeline.progress_tracker import set_progress

from io import BytesIO
import io
from motor.motor_asyncio import AsyncIOMotorClient




# Set up logging
logger = setup_logger(__name__, log_level=logging.DEBUG)
#generate_document_metadata
# Set up MongoDB connection
mongo_client = MongoClient("mongodb://mongo_custom:27017/rag_ui")
db = mongo_client["database_name"]
fs = GridFS(db)

model_manager = get_model_manager() 


# app/pipeline/progress_tracker.py
progress_map = {}  # {file_id: progress_percent}


bm25_index = BM25Index("./bm25_index_store", True)

def get_gridfs():
    """Create a new GridFS instance for thread-safe access."""
    return fs





def chunk_document(pages: list[str], metadata: dict, chunk_size=500, overlap=100) -> list[dict]:
    """
    Chunk the full document (combined pages) into meaningful pieces using LangChain splitter.
    Includes document-level metadata with each chunk.
    Returns:
        A list of dicts with: chunk_id, text, page=None (not tracked per page), metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", "", "."]
    )
    full_text = "\n".join(pages).strip()
    chunks = text_splitter.split_text(full_text)
    logger.info(f"Document chunked into {len(chunks)} pieces")
    chunked_with_metadata = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"chunk_{i}"
        assert isinstance(chunk, str), f"Chunk {i} is not a string: {type(chunk)}"
        chunked_with_metadata.append({
            "chunk_id": chunk_id,
            "text": chunk,
            "metadata": metadata
        })
        logger.debug(f"Chunk {i}: {chunk[:100]}...")
    return chunked_with_metadata




def process_uploaded_document(file_id_str):
    try:
        file_id = file_id_str
        logger.info(f"Starting to process document with ID {file_id}")

        fs = get_gridfs()
        fs_files = db.fs.files 

        if not fs.exists(file_id):
            logger.error(f"File with ID {file_id} does not exist in GridFS")
            return

        grid_file = fs.get(file_id)
        file_content = grid_file.read()

        logger.info(f"Retrieved document from MongoDB, size: {len(file_content)} bytes")

        page_texts = process_document(file_content)
        # set_progress(file_id_str, 20)

        # model_name = model_manager.initialize_gemma_model()
        model_name = "qwen2.5:1.5b"
        # set_progress(file_id_str, 40)

        metadata = generate_document_metadata(page_texts, model_name)
        # set_progress(file_id_str, 60)

        if page_texts is None:
            logger.warning("No text extracted from document")
            return

        chunks = chunk_document(page_texts, metadata)
        # set_progress(file_id_str, 80)

        logger.info(f"Document chunked into {len(chunks)} pieces")

        logger.info(f"Document chunks {chunks} ")


        chroma_add_chunks(chunks, file_id)
        # set_progress(file_id_str, 100)

        # ✅ Mark this file as completed
        fs_files.update_one(
            {"_id": file_id},
            {"$set": {"metadata.status": "completed"}}
        )



    except Exception as e:
        logger.error(f"Error processing document with ID {file_id_str}: {e}")
        logger.exception("Full traceback:")
        set_progress(file_id_str, -1)

        fs_files = db().fs.files
        fs_files.update_one(
            {"_id": file_id_str},
            {"$set": {"metadata.status": "failed"}}
        )



def extract_zip_and_store_files(file_id: str):
    def worker(zip_info, inner_content: bytes):
        try:
            inner_hash = hashlib.sha256(inner_content).hexdigest()

            if not fs.exists({"_id": inner_hash}):
                fs.put(
                    io.BytesIO(inner_content),
                    _id=inner_hash,
                    filename=zip_info.filename,
                    metadata={
                        "source_zip_id": file_id,
                        "original_filename": zip_info.filename,
                        "contentType": "application/octet-stream",  # detect later
                        "status": "pending",
                    },
                )
                logger.info(f"Stored extracted file: {zip_info.filename} with ID: {inner_hash}")
            else:
                logger.info(f"Skipped duplicate extracted file: {zip_info.filename}")

            # Call your downstream document processor
            process_uploaded_document(inner_hash)

        except Exception as e:
            logger.error(f"❌ Error in worker for file {zip_info.filename}: {e}", exc_info=True)

    try:
        logger.info(f"Starting unzip process for ZIP GridFS ID: {file_id}")

        # Step 1: Read ZIP content from GridFS
        zip_bytes = fs.get(file_id).read()
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))

        for zip_info in zip_file.infolist():
            if zip_info.is_dir():
                continue  # Skip directories

            with zip_file.open(zip_info) as inner_file:
                inner_content = inner_file.read()

                # Start a new thread to handle this file
                thread = threading.Thread(
                    target=worker,
                    args=(zip_info, inner_content),
                    daemon=True  # Set to False if you want threads to complete before exit
                )
                thread.start()

        logger.info(f"✅ Spawned all threads for ZIP file {file_id}")

    except Exception as e:
        logger.error(f"❌ Error processing ZIP file {file_id}: {e}", exc_info=True)