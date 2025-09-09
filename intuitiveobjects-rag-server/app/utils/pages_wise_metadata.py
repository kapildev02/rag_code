import re
import ast
import pickle
from typing import List, Dict, Optional, Iterator
from pathlib import Path
import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os

import logging
logging.getLogger("chromadb").setLevel(logging.WARNING) # Suppress ChromaDB logs

from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import document_collection,organization_file_collection, connect_to_mongodb
from app.core.rabbitmq_client import rabbitmq_client
import json
from app.core.config import settings
from app.services.organization_admin_services import get_updated_app_config,get_organization_app_configs

from pathlib import Path
BM25_STORE = "app/pipeline/bm25_store"
Path(BM25_STORE).mkdir(parents=True, exist_ok=True)

from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import nltk
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

nltk.download("punkt")          # sentence & word tokenization
nltk.download("punkt_tab")      # (needed in NLTK 3.8+ for multilingual)
nltk.download("stopwords") 

stop_words = set(stopwords.words("english"))

reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


# Define the directory for ChromaDB persistence
PERSIST_DIRECTORY = "chromadb_storage"


class PDFProcessor:
    def __init__(self,  persist_directory=PERSIST_DIRECTORY):

            self.processed_files = {}
            self.indexed_files = set()
            self.persist_directory = persist_directory
            self.chunks = []
            self.chunk_size = 512
            self.overlap = 128
            self.embedding_model = self._load_embedding_model()
            self.vectorstore = None  # Will be initialized when saving documents
    
    
    def _load_embedding_model(self):

        """Load the embedding model for vector storage."""

        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def get_excerpt(self,md_text: str, max_pages: int = 20) -> str:
        """
        Split by '## Page ' markers (if present) or fallback to 10k chars
        """
        pages = md_text.split("## Page ")
        if len(pages) > 1:
            return "\n".join(pages[: max_pages + 1])
        return md_text[:10000]  # fallback

    def create_metadata(self, folder_path: str, category: str, tags: List[str], force_reprocess: bool = True) -> Iterator[Dict]:
        """Extract text from Markdown files in a folder and process them."""
        pages = []  # Store processed pages

        # # List all markdown files (page_1.md, page_2.md, etc.)
        md_files = sorted(Path(folder_path).glob("*.md"))
        for i, md_file in enumerate(md_files):
            with open(md_file, "r", encoding="utf-8") as file:
                batch = file.read()  # Read markdown content

            excerpt = self.get_excerpt(batch)
            # Extract section title, summary, and tables
            title = self._extract_section_title(excerpt)
            summary = self.summarize_page(excerpt)
            tables = self._extract_tables_from_markdown(batch)
            metadata = self._extract_dynamic_metadata(batch, tags)

            page_data = {
            'section_num': i+1,
            'category': category,
            'title': title,
            'text': batch,
            'summary': summary,
            'source': str(md_files),
            'format': 'markdown',
            'tables': tables,
            'file_metadata': metadata
        }

            pages.append(page_data)  # Store for caching
            yield page_data  # Yield processed data immediately
        # Cache processed pages
        self.processed_files[folder_path] = pages

    def _extract_section_title(self, markdown_content: str) -> Optional[str]:
        prompt = f"""Extract the main title from the following Markdown content. 
        If there is no clear title, return the best possible inferred title.\n\n
        {markdown_content}\n\nTitle:"""

        response = ollama.chat(model="gemma2:2b", messages=[{"role": "user", "content": prompt}])
        # print(f"Response: {response}")
        return response["message"]["content"].strip()

    def _extract_tables_from_markdown(self, markdown_text: str) -> List[Dict]:
        """Extract tables from markdown text."""
        table_pattern = r'\|(.+)\|\n\|([-:]+\|)+\n(\|.+\|\n)+'
        tables_raw = re.findall(table_pattern, markdown_text)
        
        tables = []
        for table_match in tables_raw:
            # Process each table
            # In a complete implementation, this would parse the markdown table format
            # into a structured representation
            tables.append({
                'raw_content': ''.join(table_match),
                'type': 'markdown_table'
            })
        # print(f'tables: {tables}')
        return tables

    def summarize_page(self,content: str, is_markdown: bool = True, model_name: str = "gemma2:2b") -> str:
        # Clean Markdown if needed
        if is_markdown:
            content = re.sub(r'#{1,6}\s|[_`]', '', content)
        content = re.sub(r'\s+', ' ', content).strip()  # Normalize spaces

        # Truncate content for processing while maintaining sentence integrity
        max_length = 3000
        if len(content) > max_length:
            truncated_content = content[:max_length]
            last_sentence = truncated_content.rfind('.')
            content = truncated_content[:last_sentence + 1] if last_sentence > 0 else truncated_content

        # Optimized Prompt for Enterprise Summarization
        prompt = f"""Extract structured metadata from the following document text to enhance retrieval accuracy. 

        Focus on:  

        1️⃣ Key Topic & Relevance:  
        - Identify the type of document context for the business.
        - Explore different avenues of businesses where this document will be useful.
        - Highlight its significance in enterprise context.

        2️⃣ Essential Information for Retrieval:  
        - Core business value that can be derived from this business intelligence.
        - Important statistical analysis, business correlation, risk metrics and impacts.
        - Any person name provided has to be acurately figured out.

        3️⃣ Context-Aware Critical and Employee Insights:  
        - Summarize practical implications and risk involved in business.
        - Ensure IT Security and Business Security information doesn't get missed.
        - There could be letter formats in which figure out senders and reciever by understanding from, to and Subject.

        📌 Guidelines:  
        - Keep the summary concise (max 300 words) but information-dense factually correct with the document.  
        - Prioritize high-yield facts relevant to examination patterns and business decisions.  
        - Structure output for easy embedding in a vector database.

        Text:  
        {content}  

        📌 Response Format:  
        - Topic: (Core Business Concept)  
        - Key Information: (Critical Insights)  
        - Organization Relevance: (How it is used in practice/exams)  
        - People names involved in the document.
        - Meta Data invlved in the document.
        """
        try:
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a Busines Consultant generating high quality content. Ensure clarity, accuracy, and structured output for database storage."},
                    {"role": "user", "content": prompt}
                ],
            )

            summary = response["message"]["content"].strip()

            # Clean the summary for storage
            summary = re.sub(r'\n+', ' ', summary)
            summary = re.sub(r'\s+', ' ', summary)

            # logging.info(f"summary >>>>>>>{summary}")

            return summary

        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            return "Summary generation failed. Please check the content and try again." 

    def _extract_dynamic_metadata(self, text: str, tags: List[str], model_name: str = "gemma2:2b") -> Dict[str, str]:

        # Normalize tags: if a single string contains commas, split it
        normalized_tags = []
        for tag in tags:
            if "," in tag:
                normalized_tags.extend([t.strip() for t in tag.split(",")])
            else:
                normalized_tags.append(tag)

        tags = normalized_tags

        """
        Dynamically extract metadata from a document based on provided tags.

        Args:
            text (str): Document text
            tags (List[str]): List of metadata fields to extract
            model_name (str): LLM model to use

        Returns:
            dict: Extracted metadata with tags as keys
        """
        default_metadata = {tag: "Unknown" for tag in tags}

        # Prepare tag-specific instructions
        tag_instructions = "\n".join([
            f"- {tag}: Extract the {tag} from the document." for tag in tags
        ])

        prompt = f"""
        Extract the following metadata as strict JSON with keys {tags}:
        {tag_instructions}

        Document:
        {text}

        Return ONLY valid JSON.
        """
        try:
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a precise document metadata extractor. Ensure clarity, accuracy, and valid JSON output."},
                    {"role": "user", "content": prompt}
                ]
            )

            raw_output = response["message"]["content"].strip()

            # Remove accidental markdown fencing
            raw_output = re.sub(r"```json|```", "", raw_output).strip()

            import json
            metadata = json.loads(raw_output)

            # Ensure all required fields are present
            for tag in tags:
                if tag not in metadata or not metadata[tag]:
                    metadata[tag] = default_metadata[tag]

            # Convert lists to comma-separated strings
            for k, v in metadata.items():
                if isinstance(v, list):
                    metadata[k] = ", ".join(map(str, v))

            # logging.info(f"Extracted dynamic metadata: {metadata}")
            return metadata

        except Exception as e:
            logging.error(f"Metadata extraction failed: {e}")
            return default_metadata
 
    def _generate_chunk_name(self, chunk_text: str) -> str:
        """Generate a descriptive name for a chunk."""
        header_match = re.search(r'^#{1,6}\s(.+)$', chunk_text.split('\n')[0])
        if header_match:
            return header_match.group(1)[:50]
        
        first_sentence = re.split(r'(?<=[.!?])\s+', chunk_text.strip())[0]
        return first_sentence if len(first_sentence) < 50 else chunk_text.strip()[:50] + "..."
        
    def create_chunks(self, pages: List[Dict]) -> List[Document]:
        """Chunk extracted pages for vector storage, returning a list of LangChain Documents."""

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
            length_function=len
        )

        documents = []
        for page in pages:
            split_texts = text_splitter.split_text(page['text'])

            for i, chunk_text in enumerate(split_texts):
                chunk_name = self._generate_chunk_name(chunk_text)

                # Create basic metadata
                chunk_metadata = {
                    'summary': str(page.get('summary', '')),
                    'title': str(page.get('title', '')),
                    'section_num': str(page.get('section_num', '')),
                    'chunk_id': len(documents),
                    'source': str(page['source']),
                    'format': str(page.get('format', 'text')),
                    'chunk_name': str(chunk_name),
                    'category': str(page.get('category', 'unknown')).strip().lower(),
                }

                # Handle file_metadata
                if 'file_metadata' in page:
                    # Convert file_metadata to string representation if needed
                    chunk_metadata['file_metadata'] = str(page['file_metadata'])

                # Handle tables - convert to string representation
                if 'tables' in page and page['tables']:
                    tables_str = []
                    for table in page['tables']:
                        if isinstance(table, dict):
                            table_content = table.get('raw_content', '')
                            table_type = table.get('type', '')
                            tables_str.append(f"{table_type}: {table_content}")
                    chunk_metadata['tables'] = "; ".join(tables_str)

                # Create Document with the processed metadata
                documents.append(Document(page_content=chunk_text, metadata=chunk_metadata))
        print('documents>>>>>>',documents)
        for doc in documents:
            print(doc.page_content)

        return documents
    
    def save_to_chroma(self, chunks: List[Document]):
        """Store processed chunks into ChromaDB."""
        try:
            # Ensure the persist directory exists
            if not os.path.exists(self.persist_directory):
                os.makedirs(self.persist_directory)
            if not os.access(self.persist_directory, os.W_OK):
               raise PermissionError(f"Persist directory {self.persist_directory} is not writable.")

            # Create new collection and add documents
            vectorstore = Chroma.from_documents(
                documents=chunks,
                collection_name="rag-chroma",
                embedding=self.embedding_model,
                persist_directory=self.persist_directory
            )

            # Persist changes to disk
            vectorstore.persist()

            # Store the vectorstore reference
            self.vectorstore = vectorstore

            logging.info(f"Successfully saved {len(chunks)} chunks to ChromaDB at {self.persist_directory}")

        except Exception as e:
            logging.error(f"Error saving to ChromaDB: {str(e)}")
            raise Exception(f"Failed to save documents to ChromaDB: {str(e)}")

    def _prepare_bm25_docs(self, chunks):
        """
        Convert Document chunks into list of strings for BM25 indexing.
        """
        return [chunk.page_content for chunk in chunks]



    def split_into_sentences(self,text):
        return sent_tokenize(text) 


    def chunk_sentences(self,sentences, chunk_size, overlap):
        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            words = sentence.split()
            if current_len + len(words) > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_words = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
                current_chunk = overlap_words.copy()
                current_len = sum(len(s.split()) for s in current_chunk)
            current_chunk.append(sentence)
            current_len += len(words)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    # Convert text into BM25 chunks
    def create_bm25_corpus(self, processed_pages: List[Dict], chunk_size: int = 50, overlap: int = 10):
        """
        Convert processed pages into BM25 corpus with smaller chunks.
        """
        corpus = []
        for page in processed_pages:
            text = page['text']
            sentences = self.split_into_sentences(text)
            chunks = self.chunk_sentences(sentences, chunk_size, overlap)
            corpus.extend(chunks)
        return corpus

    # Build BM25 index
    def build_bm25(self, corpus: List[str]):
        tokenized_corpus = [word_tokenize(doc.lower()) for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        return bm25, corpus, tokenized_corpus

    # Save BM25 index
    def save_bm25_index(self, doc_id: str, bm25, corpus, save_dir: str = BM25_STORE):
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{doc_id}.pkl")
        data = {
            "bm25": bm25,
            "corpus": corpus
        }
        try:
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
            logging.info(f"BM25 index saved to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save BM25 index: {e}")


    



    async def index_pdf(self, folder_path: str, category: str, doc_id: str, user_id: str, tags: List[str], force_reindex: bool = False):
        print(f"Using model: {self.embedding_model} to index {folder_path}")

        """Process and index a PDF file by extracting, chunking, and storing embeddings.

    Args:
            folder_path (str): Path to the PDF file or folder to index
            force_reindex (bool): If True, reindex even if already indexed

        Returns:
            None

        Raises:
            FileNotFoundError: If the folder path doesn't exist
            Exception: For other processing errors
        """
        try:
            # Validate input path
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"Path does not exist: {folder_path}")

            # Check if already indexed
            if folder_path in self.indexed_files and not force_reindex:
                logging.info(f"File {folder_path} already indexed. Use force_reindex=True to reindex.")
                return

            logging.info(f"Starting indexing process for {folder_path}...")

            # Extract metadata
            try:

                processed_pages = list(self.create_metadata(folder_path, category, tags))
                if not processed_pages:
                    raise ValueError(f"No pages were processed from {folder_path}")
                # logging.info(f"Extracted metadata: {processed_pages}")
                logging.info(f"Successfully extracted metadata from {len(processed_pages)} files")
            except Exception as e:
                raise Exception(f"Error in metadata extraction: {str(e)}")

            await document_collection().update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "current_stage": "TEXT_CHUNKS_CREATION_STARTED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "TEXT_CHUNKS_CREATION_STARTED",
                            "status": "completed",
                            "timestamp": datetime.now(),
                            "error_message": None,
                            "retry_count": 0
                        }
                    }
                }
            )
            await rabbitmq_client.send_message(
                settings.NOTIFY_QUEUE,
                json.dumps({
                    "event_type": "document_notify",
                    "doc_id": doc_id,
                    "user_id": user_id,
                })
            )
            # Create chunks
            try:
                chunks = self.create_chunks(processed_pages)
                if not chunks:
                    raise ValueError(f"No chunks were created from {folder_path}")
                logging.info(f"Successfully created {len(chunks)} chunks")
                # # Log each chunk's metadata and a preview of its content
                # for idx, chunk in enumerate(chunks):
                #     logging.info(f"Chunk {idx+1}: Metadata: {chunk.metadata} | Content Preview: {chunk.page_content[:100]}...")
            except Exception as e:
                raise Exception(f"Error in chunk creation: {str(e)}")

            await document_collection().update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "current_stage": "TEXT_CHUNKS_CREATION_COMPLETED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "TEXT_CHUNKS_CREATION_COMPLETED",
                            "status": "completed",
                            "timestamp": datetime.now(),
                            "error_message": None,
                            "retry_count": 0
                        }
                    }
                }
            )
            # Save to ChromaDB
            try:
                self.save_to_chroma(chunks)
               
                logging.info(f"Successfully stored chunks in ChromaDB")
            except Exception as e:
                raise Exception(f"Error saving to ChromaDB: {str(e)}")


                        # Save BM25 index for keyword search
            try:



                # 1️⃣ Create Chroma chunks
                chunks = self.create_chunks(processed_pages)  # Uses self.chunk_size for embeddings

                # # 2️⃣ Save to Chroma
                # self.save_to_chroma(chunks)

                # 3️⃣ Create BM25 corpus with smaller chunks
                bm25_corpus = self.create_bm25_corpus(processed_pages, chunk_size=50, overlap=10)
                bm25, corpus, tokenized_corpus = self.build_bm25(bm25_corpus)
                self.save_bm25_index(doc_id, bm25, corpus, save_dir=BM25_STORE)



                logging.info(f"BM25 index created for {folder_path}")
            except Exception as e:
                logging.error(f"Failed to save BM25 index for {folder_path}: {e}")


            await document_collection().update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "current_stage": "VECTORS_STORED",
                        "updated_at": datetime.now(),
                    },
                    "$push": {
                        "status_history": {
                            "stage": "VECTORS_STORED",
                            "status": "completed",
                            "timestamp": datetime.now(),
                            "error_message": None,
                            "retry_count": 0
                        }
                    }
                }
            )
            
            await rabbitmq_client.send_message(
                settings.NOTIFY_QUEUE,
                json.dumps({
                    "event_type": "document_notify",
                    "doc_id": doc_id,
                    "user_id": user_id,
                })
            )
            
            # Update indexed files set
            self.indexed_files.add(folder_path)

            # Save indexed files list to persist between runs (optional)
            self._save_indexed_files()

            logging.info(f"Successfully completed indexing of {folder_path} with {len(chunks)} chunks")

        except Exception as e:
            logging.error(f"Error indexing {folder_path}: {str(e)}")
            raise

    def _save_indexed_files(self):
        """Save the set of indexed files to a persistent storage."""
        try:
            index_file = os.path.join(self.persist_directory, 'indexed_files.txt')
            with open(index_file, 'w') as f:
                for file_path in self.indexed_files:
                    f.write(f"{file_path}\n")
        except Exception as e:
            logging.warning(f"Failed to save indexed files list: {str(e)}")

    async def setup_retrieval_qa(self, model_name: str = "llama2"):
        """Setup the retrieval QA system using Ollama."""

      
        try:
            # Use existing vectorstore if available, otherwise create new one
            if self.vectorstore is None:
                self.vectorstore = Chroma(
                    collection_name="rag-chroma",
                    embedding_function=self.embedding_model,
                    persist_directory=self.persist_directory
                )

            # Create retriever
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )

            # Initialize Ollama LLM
            llm = Ollama(
                model=model_name,
                temperature=0.1
            )

            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )

            return True

        except Exception as e:
            logging.error(f"Error setting up QA system: {str(e)}")
            return False

    def filter_chunks_by_keywords(self, chunks, keywords):
        """
        Filter chunks based on keywords present in file_metadata or content.
        If no matches are found, return all chunks.
        Args:
            chunks: List of Document (or dict) objects
            keywords: List of keywords to search for (case-insensitive)
        Returns:
            List of matching chunks (or all chunks if no match found)
        """
        matched_chunks = []

        for doc in chunks:
            meta_match = False
            content_match = False

            # 1️⃣ Check file_metadata
            file_meta_str = doc.metadata.get("file_metadata", "")
            if file_meta_str:
                try:
                    file_meta = ast.literal_eval(file_meta_str)
                except Exception:
                    file_meta = {}

                for val in file_meta.values():
                    for k in keywords:
                        if k.lower() in str(val).lower():
                            meta_match = True
                            print(f"Matched keyword '{k}' in value: {val}")
                            break
                    if meta_match:
                        break

            # 2️⃣ Check content if not matched in metadata
            if not meta_match:
                content_text = getattr(doc, "page_content", "") or ""
                for k in keywords:
                    if k.lower() in content_text.lower():
                        content_match = True
                        print(f"[Content Match] Keyword '{k}' found in content: {content_text[:100]}...")
                        break

            # 3️⃣ Include chunk if match found
            if meta_match or content_match:
                matched_chunks.append(doc)

        # 4️⃣ Fallback → if nothing matched, return all chunks
        if not matched_chunks:
            print("⚠️ No keyword matches found — returning all chunks instead.")
            return chunks

        return matched_chunks




    async def ask_question(self, user_id: str, question: str, model_name: str = "gemma2:2b") -> dict:
        """
        Ask a question and get an answer from the indexed documents.
        Handles both Chroma (Document objects) and BM25 (dict) results.
        """

        print("Fetching organization user for user_id:", user_id)

        from app.db.mongodb import organization_user_collection
        existing_user = await organization_user_collection().find_one({"_id": ObjectId(user_id)})
        organization_id = existing_user.get("organization_id")
        print("Fetching organization users for organization_id:", organization_id)

        # 🔹 Load organization-specific config
        config = await get_updated_app_config(organization_id)
        model_name = config.get("llm_model", "qwen2.5:1.5b")
        embedding_model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        temperature = config.get("temperature", 0.7)

        category_id = existing_user.get("category_id", None)
        user_category = "unknown"
        if category_id:
                from app.db.mongodb import category_collection
                category_doc = await category_collection().find_one({"_id": ObjectId(category_id)})
                if category_doc:
                    user_category = category_doc.get("name", "unknown")

        logging.info(f"Category ID: {category_id}, User Category: {user_category}")
        logging.info(f"Using model: {model_name}, temperature: {temperature}")

        # keyword_extractor = KeywordExtractor()
        # metadata_query_result = keyword_extractor.extract_keywords(question, top_n=10)
        metadata_query_result =  [w for w in word_tokenize(question.lower()) if w not in stop_words]

        print(f'metadata_query_result: {metadata_query_result}')

        try:
            # 🔹 Retrieve docs from vectorstore
            vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=HuggingFaceEmbeddings(model_name=embedding_model),
                persist_directory=self.persist_directory
            )

            all_docs = vectorstore.similarity_search("test", k=100)
            logging.info(f"All document categories: {set([doc.metadata.get('category') for doc in all_docs])}")

            # Log the category we're filtering for
            logging.info(f"Filtering for category: {user_category.strip().lower()}")
            
            # First try category-specific search
            try:
                retrieved_docs = vectorstore.max_marginal_relevance_search(
                    question,
                    k=5,
                    fetch_k=16,
                    lambda_mult=0.7,
                    filter={"category": user_category.strip().lower()}
                )
            except Exception as filter_error:
                logging.warning(f"Error with filtered search: {str(filter_error)}")
                # Fallback to unfiltered search
                retrieved_docs = vectorstore.max_marginal_relevance_search(
                    question,
                    k=5,
                    fetch_k=16,
                    lambda_mult=0.7
                )

            print("Retrieved docs from Chroma:", len(retrieved_docs))

            # 🔹 Filter by keywords
            filtered_chunks = self.filter_chunks_by_keywords(retrieved_docs, metadata_query_result)

            for i, doc in enumerate(filtered_chunks, start=1):
                print(f"\n--- Matched Chunk {i} ---")
                print("ID:", doc.id)
                print("Metadata:", doc.metadata)
                print("Content:\n", doc.page_content)

            
            # 🔹 Convert Document → dict for uniformity
            def convert_doc_to_dict(doc):
                return {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "chunk_id": doc.metadata.get("chunk_id", None),
                    "score": None  # no vector score yet
                }

            filtered_dicts = [convert_doc_to_dict(doc) for doc in filtered_chunks]
            print(len(filtered_dicts), 'filtered_dicts>>>>>>')
            len_filtered_dicts = len(filtered_dicts)

            # print(f'Filtered chunks: {filtered_dicts}')


            model = SentenceTransformer("all-MiniLM-L6-v2")
            candidate_embeddings = model.encode(filtered_dicts, convert_to_tensor=True)
            query_embedding = model.encode(question, convert_to_tensor=True)

            # Cosine similarity
            cos_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
            print("cos_scores", cos_scores)
            top_results = cos_scores.topk(k = len_filtered_dicts)
            print("top_results", top_results)
            chroma_dicts = [filtered_dicts[idx] for idx in top_results.indices]




            for i, idx in enumerate(top_results.indices, start=1):
                doc = chroma_dicts[idx]
                print(f"\n--- Top Filtered Chunk {i} ---")
                print("ID:", doc.get("chunk_id", "N/A"))
                print("Metadata:", doc.get("metadata", "N/A"))
                print("Content:\n", doc.get("text", ""))



            

            # 🔹 Run BM25 keyword search (already dicts)
            candidate_chunks = run_bm25_keyword_search(metadata_query_result)
            print(f'BM25 chunks: {candidate_chunks}')
            for i, chunk in enumerate(candidate_chunks, start=1):
                print(f"\n--- BM25 Chunk {i} ---")
                print("Content:\n", chunk['text'])

            len_candidate_chunks = len(candidate_chunks)


            model = SentenceTransformer("all-MiniLM-L6-v2")
            candidate_embeddings = model.encode(candidate_chunks, convert_to_tensor=True)
            query_embedding = model.encode(question, convert_to_tensor=True)

            # Cosine similarity
            cos_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
            top_results = cos_scores.topk(k = len_candidate_chunks)

            # Final top chunks
            bm25_dicts = [candidate_chunks[idx] for idx in top_results.indices] 

            print(f"Top BM25 chunks after re-ranking: {bm25_dicts}") 

            print("Printing BM25 chunks separately:")

            for i, chunk in enumerate(bm25_dicts, start=1):
                print(f"--- BM25 Chunk {i} ---")
                print(chunk['text'])


            

            # 🔹 Combine both sources
            top_chunks = filtered_dicts + bm25_dicts

            len_top_chunks = len(top_chunks)


            model = SentenceTransformer("all-MiniLM-L6-v2")
            candidate_embeddings = model.encode(top_chunks, convert_to_tensor=True)
            query_embedding = model.encode(question, convert_to_tensor=True)

            # Cosine similarity
            cos_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
            top_results = cos_scores.topk(k = len_top_chunks)

            # Final top chunks
            ranked_chunks = [top_chunks[idx] for idx in top_results.indices] 



            def format_chunk_for_context(chunk: dict) -> str:
                metadata = chunk.get("metadata", {})
                chunk_id = chunk.get("chunk_id", "N/A")
                source = metadata.get("source", "Unknown")
                title = metadata.get("title", "")
                section = metadata.get("section_num", "")
                file_meta = metadata.get("file_metadata", "")

                return (
                    f"[Chunk ID: {chunk_id} | Source: {source} | Title: {title} | Section: {section}]\n"
                    f"File Metadata: {file_meta}\n"
                    f"Content:\n{chunk.get('text', '')}"
    )




            # 🔹 Create context for LLM
            # context = "\n\n".join([chunk["text"] for chunk in ranked_chunks]) 

            context = "\n\n".join([format_chunk_for_context(chunk) for chunk in ranked_chunks])
            print("Context for LLM:\n", context)

            prompt = f"""
            You are a helpful assistant. 
            Use BOTH the **content** and the **metadata** from the following chunks to answer the question.

            Context Chunks:
            {context}

            Question: {question}

            Provide a comprehensive answer based ONLY on the provided context.
            If the context doesn’t contain enough information, say so explicitly.
            """

            # 🔹 Query Ollama
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature}
            )

            # 🔹 Format response
            result = {
                "answer": response.get("message", {}).get("content", "").strip(),
                "sources": []
            }
            
        #     # Add source information
            for doc in retrieved_docs:
                source = {
                    "file": doc.metadata.get("source", "Unknown").split("/")[-1],  # just filename
                    # "title": doc.metadata.get("title", "").replace("**", "").replace("\n", " ").strip(),
                    # "content": doc.page_content[:200] + "...",  # First 200 chars
                    # "metadata": doc.metadata
                }
                result["sources"].append(source)

            
            return result

             
        except Exception as e:
            logging.error(f"Error in question answering: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": [],
                "error": str(e)
            }

    def search_similar(self, query: str, n_results: int = 3):
        """
            Search for similar content using sentence transformers embeddings.

            Args:
                query (str): The search query
                n_results (int): Number of results to return
        """
        try:
            vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory
            )

            results = vectorstore.similarity_search_with_score(query, k=n_results)
            # print("Resultant Chunks ----------------------",results)
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                })

            return formatted_results

        except Exception as e:
            logging.error(f"Error in similarity search: {str(e)}")
            return {"error": str(e)}
            


processor = PDFProcessor()



def run_bm25_keyword_search(query: List[str], bm25_dir="./app/pipeline/bm25_store", top_n: int = 5) -> List[Dict]:
    """
    Performs BM25 keyword search across all saved indexes.
    Returns top-N results globally across all indexes.
    """
    bm25_chunks = []
    print(f"Running BM25 keyword search for query: {query}")
    if not os.path.isdir(bm25_dir):
        print(f"BM25 directory not found: {bm25_dir}")
        return []

    # Tokenize query (very basic split; replace with better NLP if needed)
    # query_tokens = query.lower().split()

    query_tokens = [q.lower() for q in query]

    # Loop through all saved BM25 indexes
    for filename in os.listdir(bm25_dir):
        if not filename.endswith(".pkl"):
            continue

        file_path = os.path.join(bm25_dir, filename)

        try:
            # with open(file_path, "rb") as f:
            # with open(file_path, "rb") as f:
            #     pickle.dump({"bm25": bm25, "corpus": corpus}, f)

            #     data = pickle.load(f)
            #     bm25 = data["bm25"]
            #     corpus = data["corpus"]

            with open(file_path, "rb") as f:
                data = pickle.load(f)
                bm25 = data["bm25"]

                # Try to get corpus from pickle, else fallback
                corpus = data.get("corpus") or getattr(bm25, "corpus", None)

                if corpus is None:
                    print(f"⚠️ Skipping {filename}: no corpus found")
                    continue


            # Run BM25 search on this corpus
            top_results = bm25.get_top_n(query_tokens, corpus, n=top_n)

            for text in top_results:
                bm25_chunks.append({
                    "text": text,
                    # "source": filename  # which pickle file it came from
                })

        except Exception as e:
            print(f"Failed to process BM25 index for {filename}: {e}")

    # Deduplicate & rank (BM25 already returns ranked chunks, but across files we need global selection)
    unique_chunks = []
    seen_texts = set()
    for chunk in bm25_chunks:
        if chunk["text"] not in seen_texts:
            unique_chunks.append(chunk)
            seen_texts.add(chunk["text"])

    # Only keep top N globally
    return unique_chunks[:top_n]

def rerank_results(query: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Reranks chunks using a cross-encoder model based on relevance to the query.
    Filters out chunks below min_score if specified.
    """
    if not chunks:
        return []

    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = reranker_model.predict(pairs)

    for i, score in enumerate(scores):
        chunks[i]["rerank_score"] = float(score)

    sorted_chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    # if min_score is not None:
    #     sorted_chunks = [chunk for chunk in sorted_chunks if chunk["rerank_score"] >= min_score]

    return sorted_chunks[:top_k]









def interactive_qa():
    print("\n=== Interactive Q&A System ===")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'switch model' to change the model")
    print("Type 'search' to find similar content")
    print("================================\n")

    current_model = "gemma3:4b"

    while True:
        # Get user input
        user_input = input("\nEnter your question (or command): ").strip()

        # Check for exit commands
        if user_input.lower() in ['quit', 'exit']:
            print("\nThank you for using the Q&A system!")
            break

        # Check for search command
        if user_input.lower() == 'search':
            search_query = input("Enter search query: ").strip()
            try:
                results = processor.search_similar(search_query, n_results=3)

                print("\n=== Similar Content ===")
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"Content: {result['content'][:200]}...")
                    print(f"Source: {result['metadata']['source']}")
                    print(f"Similarity Score: {result['similarity_score']}")
                    print("-" * 50)
                continue
            except Exception as e:
                print(f"\nError in search: {str(e)}")
                continue

        # Check for model switch command
        if user_input.lower() == 'switch model':
            models = ['gemma3:1b', 'llama2', 'mistral', 'neural-chat']
            print("\nAvailable models:", ', '.join(models))
            new_model = input("Enter model name: ").strip()
            if new_model in models:
                current_model = new_model
                print(f"Switched to model: {current_model}")
            else:
                print("Invalid model name. Keeping current model.")
            continue

        # Handle regular questions
        if user_input:
            try:
                # Get answer
                result = processor.ask_question(user_input, model_name=current_model)

                # Print the response
                print("\n=== Answer ===")
                print(result['answer'])

                # Print sources
                print("\n=== Sources ===")
                for source in result['sources']:
                    print(f"- {source['metadata']['source']}")
                    print(f"  Context: {source['content']}...")

                print("\n" + "="*50)

            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try again with a different question or model.")

# Start the interactive session
if __name__ == "__main__":
    interactive_qa()
