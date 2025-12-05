import re
import asyncio
import ast
import pickle
from typing import List, Dict, Optional, Iterator, AsyncIterator
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
# from langchain_chroma import Chroma
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
from sentence_transformers import CrossEncoder, SentenceTransformer
from app.db.mongodb import organization_user_collection, category_collection
from rank_bm25 import BM25Okapi
import nltk
from sentence_transformers import util
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
nltk.download("punkt")          # sentence & word tokenization
nltk.download("punkt_tab")      # (needed in NLTK 3.8+ for multilingual)
nltk.download("stopwords") 
stop_words = set(stopwords.words("english"))
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nLoading models on {DEVICE.upper()}...")
reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    cache_folder="./models/cross_encoder",
    device=DEVICE
)

sentence_transformer = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./models/sentence_transformer",
    device=DEVICE
)

# Define the directory for ChromaDB persistence
PERSIST_DIRECTORY = "chromadb_storage"

class PDFProcessor:
    def __init__(self,  persist_directory=PERSIST_DIRECTORY):

            self.processed_files = {}
            self.indexed_files = set()
            self.persist_directory = persist_directory
            self.chunks = []
            self.chunk_size = 1000
            self.overlap = 150
            self.embedding_model = self._load_embedding_model()
            self.vectorstore = None  # Will be initialized when saving documents
    
    
    def _load_embedding_model(self):
        """Load the embedding model for vector storage."""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder="./models/embeddings",
            model_kwargs={'device': DEVICE}  # Use GPU if available
        )

    def _numeric_sort_key(self, filename: Path) -> float:
        """Extract page number for numeric sorting of filenames."""
        try:
            # Extract the number from filename (e.g., 'page_1.md' -> 1)
            name_parts = filename.stem.rsplit('_', 1)
            if len(name_parts) == 2 and name_parts[1].isdigit():
                return int(name_parts[1])
            return float('inf')  # For files without numbers
        except (ValueError, IndexError):
            return float('inf')


    async def create_metadata(self,folder_path: str,category: str,tags: List[str],doc_id: str,user_id: str,force_reprocess: bool = True) -> AsyncIterator[Dict]:
        """Extract text and contextual metadata from Markdown files in a folder or subfolders."""
        pages = []
        last_metadata = None
        folder_path = Path(folder_path)

        subfolders = [f for f in folder_path.iterdir() if f.is_dir()]

        # Choose iteration target
        folder_targets = sorted(subfolders) if subfolders else [folder_path]

        for target_folder in folder_targets:
            md_files = sorted(target_folder.glob("*.md"), key=self._numeric_sort_key)
            subfolder_pages = []

            for i, md_file in enumerate(md_files, 1):
                try:
                    with open(md_file, "r", encoding="utf-8") as f:
                        batch = f.read().strip()

                    content = self._extract_section_title_with_context(last_metadata, batch)
                    last_metadata = content
                    print(content)
                    tables = self._extract_tables_from_markdown(batch)

                    title = content.get("title", "Untitled").strip() or "Untitled"
                    section_title = content.get("section_title", "").strip() or title
                    page_data = {
                        "section_num": i,
                        "category": category,
                        "title": title,
                        "section_title": section_title,
                        "summary": content.get("summary", "Content available").strip(),
                        "text": batch,
                        "source": str(md_file),
                        "format": "markdown",
                        "tables": tables,
                    }
                    await rabbitmq_client.send_message(
                        settings.NOTIFY_QUEUE,
                        json.dumps({
                            "event_type": "document_notify",
                            "doc_id": doc_id,
                            "user_id": user_id,
                        })
                    )

                    subfolder_pages.append(page_data)
                    yield page_data

                except Exception as e:
                    logging.error(f"Error processing file {md_file}: {e}")
                    continue
            last_metadata = None
            pages.extend(subfolder_pages)

        # Cache final processed pages
        self.processed_files[folder_path] = pages
    def _extract_section_title_with_context(self, prev_metadata: Optional[Dict[str, str]], current_markdown: str) -> Dict[str, str]:
        """
        Detect whether current markdown continues previous section or introduces a new one.
        Returns concise title(s), section title, and contextual summary.
        """

        prev_title = prev_metadata.get("title") if prev_metadata else "None"
        prev_summary = prev_metadata.get("summary") if prev_metadata else "None"
        
        if prev_title :
            prev_title = prev_title.split(" > ")[-1]  # Get the last part of the hierarchical title

        # Build prompt using safe concatenation to avoid accidental interpretation of
        # literal braces inside f-strings (which causes "Invalid format specifier" errors).
        prompt = (
            "You are analyzing two consecutive markdown pages extracted from a context.\n\n"
            "Previous page metadata:\n"
            "Title: " + str(prev_title) + "\n"
            "Summary: " + str(prev_summary) + "\n\n"
            "Current page markdown:\n'''"
            + current_markdown +
            "'''\n\n"
            "Rules:\n"
            "1. If this page clearly continues the same section (same exam, same topic), keep the same title.\n"
            "2. If it introduces a new section (e.g., new body part, new screening, or 'IMPRESSION'), include both titles:\n"
            "- First: previous (if still relevant)\n"
            "- Second: the new heading found on this page\n"
            "3. If the page only has a new section unrelated to the previous, output only that new title.\n"
            "4. Do NOT repeat older sections that are not relevant anymore.\n"
            "5. Return valid JSON only in this format:\n\n"
            "{\n"
            '"titles": ["relevant titles only"],\n'
            '"section_title": "Most relevant section title on this page.",\n'
            '"summary": "Brief 2–3 line summary of this page."\n'
            "}\n"
        )


        try:
            response = ollama.chat(
                model="gemma2:2b",
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract clean JSON
            content = (
                response.get("message", {}).get("content")
                or response.get("messages", [{}])[0].get("content", "")
            ).strip()
            content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                content = match.group(0)

            result = json.loads(content)

            titles = result.get("titles", [])
            if isinstance(titles, str):
                titles = [titles]

            return {
                "title": " > ".join(titles),
                "section_title": result.get("section_title", titles[-1] if titles else "Untitled").strip(),
                "summary": result.get("summary", "Content available").strip()
            }

        except Exception as e:
            logging.error(f"Error parsing LLM output: {e}")
            return {
                "title": prev_title if prev_title != "None" else "Untitled",
                "section_title": prev_title if prev_title != "None" else "Untitled",
                "summary": "Content available"
            }

    def _extract_tables_from_markdown(self, markdown_text: str) -> List[Dict]:
        """Extract markdown tables into structured dictionaries."""
        table_pattern = r'\|(.+)\|\n\|([-:]+\|)+\n(\|.+\|\n)+'
        tables_raw = re.findall(table_pattern, markdown_text)

        tables = []
        for table_match in tables_raw:
            tables.append({
                "raw_content": ''.join(table_match),
                "type": "markdown_table"
            })
        return tables


    def _extract_dynamic_metadata(self,text: str,tags: List[str],model_name: str ) -> Dict[str, str]:
            """
            Extract only the requested metadata tags from a given text using an LLM.
            Returns a dict with tag names as keys and extracted values as strings.
            """
            if not model_name:
                model_name = "phi4-mini:3.8b"
            # Normalize tag list (handle comma-separated input)
            print(f"model_name in _extract_dynamic_metadata: {model_name}")
            normalized_tags = []
            for tag in tags:
                if "," in tag:
                    normalized_tags.extend([t.strip() for t in tag.split(",")])
                else:
                    normalized_tags.append(tag)
            tags = normalized_tags

            default_metadata = {tag: "Unknown" for tag in tags}

            # Build the instruction string dynamically
            tag_instructions = "\n".join(
                [f'- "{tag}": Extract the {tag} from the document.' for tag in tags]
            )

            prompt = f"""
            You are a precise document metadata extractor.
            Extract only the following metadata fields from the document below:

            {tag_instructions}

            Rules:
            - Output must be a JSON object with **only** these keys: {tags}.
            - All values must be plain strings.
            - If a value is not found, use "Unknown".
            - Do not include explanations, markdown, or code fences.
            - Use double quotes for all keys and values.

            Document:
            \"\"\"{text}\"\"\"

            Return only valid JSON.
            """

            try:
                response = ollama.chat(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON metadata extractor. Output only valid JSON with the requested keys."},
                        {"role": "user", "content": prompt},
                    ],
                )

                raw_output = (
                    response.get("message", {}).get("content")
                    or response.get("messages", [{}])[0].get("content", "")
                ).strip()

                # Clean code fences and trailing commas
                raw_output = re.sub(r"^```(?:json)?|```$", "", raw_output, flags=re.MULTILINE).strip()
                raw_output = re.sub(r",(\s*[}\]])", r"\1", raw_output)

                # Extract JSON portion
                start, end = raw_output.find("{"), raw_output.rfind("}") + 1
                if start != -1 and end != -1:
                    raw_output = raw_output[start:end]

                try:
                    metadata = json.loads(raw_output)
                except Exception:
                    logging.warning(f"Model returned invalid JSON. Output:\n{raw_output}")
                    return default_metadata

                # Keep only requested tags and fill missing ones
                clean_metadata = {}
                for tag in tags:
                    value = metadata.get(tag, "Unknown")
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    clean_metadata[tag] = str(value).strip() or "Unknown"

                return clean_metadata

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

    def create_chunks(self, folder_path: str, tags: List[str],model_name: str, pages: List[Dict]) -> List[Document]:
        """Chunk extracted pages for vector storage with hierarchical metadata."""
        
        # Extract file-level metadata
        file_metadata = {}
        
        # Check if the folder has subfolders (ZIP case)
        subfolders = [f for f in Path(folder_path).iterdir() if f.is_dir()]
        
        if subfolders:
            # ZIP file case - handle each subfolder
            try:
                subfolder_metadata = {}
                for subfolder in subfolders:
                    combined_text = ""
                    md_files = sorted(subfolder.glob("*.md"))
                    
                    # Only process if folder contains markdown files
                    if not list(md_files):
                        continue
                        
                    # Combine all text from the subfolder
                    for md_file in sorted(subfolder.glob("*.md")):
                        try:
                            with open(md_file, "r", encoding="utf-8") as f:
                                combined_text += f.read() + "\n\n"
                        except Exception as e:
                            logging.error(f"Error reading file {md_file}: {e}")
                            continue
                    
                    if combined_text.strip():  # Only process if there's actual content
                        metadata = self._extract_dynamic_metadata(combined_text, tags=tags, model_name=model_name)
                        subfolder_metadata[str(subfolder)] = metadata
                        logging.info(f"Extracted metadata for subfolder {subfolder.name}")
                    
                file_metadata = subfolder_metadata
                
            except Exception as e:
                logging.error(f"Error processing ZIP subfolders: {e}")
                file_metadata = {}
                
        else:
            # Single file case
            try:
                combined_text = ""
                for md_file in sorted(Path(folder_path).glob("*.md")):
                    with open(md_file, "r", encoding="utf-8") as f:
                        combined_text += f.read() + "\n\n"
                        
                if combined_text.strip():
                    file_metadata = self._extract_dynamic_metadata(combined_text, tags=tags , model_name=model_name)
                    logging.info("Extracted metadata for single file")
                    
            except Exception as e:
                logging.error(f"Error extracting metadata from single file: {e}")
                file_metadata = {}

        # Create text splitter for chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
            length_function=len
        )

        # Process pages and create chunks
        documents = []
        for page in pages:
            source_path = Path(page['source'])
            parent_folder = str(source_path.parent)
            
            # Get appropriate metadata
            metadata = (file_metadata.get(parent_folder, file_metadata) 
                    if isinstance(file_metadata, dict) else {})
            
            # Create chunks
            split_texts = text_splitter.split_text(page['text'])
            
            for i, chunk_text in enumerate(split_texts):
                chunk_name = self._generate_chunk_name(chunk_text)
                
                chunk_metadata = {
                    'summary': str(page.get('summary', '')),
                    'title': str(page.get('title', '')),
                    'section_title': str(page.get('section_title', '')),
                    'section_num': str(page.get('section_num', '')),
                    'chunk_id': len(documents),
                    'source': str(page['source']),
                    'format': str(page.get('format', 'text')),
                    'chunk_name': str(chunk_name),
                    'category': str(page.get('category', 'unknown')).strip().lower(),
                    'file_Tags': str(metadata),
                }

                if 'tables' in page and page['tables']:
                    tables_str = []
                    for table in page['tables']:
                        if isinstance(table, dict):
                            table_content = table.get('raw_content', '')
                            table_type = table.get('type', '')
                            tables_str.append(f"{table_type}: {table_content}")
                    chunk_metadata['tables'] = "; ".join(tables_str)

                documents.append(Document(
                    page_content=chunk_text, 
                    metadata=chunk_metadata
                ))

        return documents
            
    def save_to_chroma(self, chunks: List[Document]):
        """Store processed chunks into ChromaDB."""
        try:
            # Ensure the persist directory exists
            if not os.path.exists(self.persist_directory):
                os.makedirs(self.persist_directory)

            # Create new collection and add documents
            vectorstore = Chroma.from_documents(
                documents=chunks,
                collection_name="rag-chroma",
                embedding=self.embedding_model,
                persist_directory=self.persist_directory
            )

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
        texts=[]
        corpus = []
        for page in processed_pages:
            text = page['text']
            category = page.get('category', 'unknown').strip().lower()
            source = page.get('source', 'unknown').strip().lower()
            sentences = self.split_into_sentences(text)
            chunks = self.chunk_sentences(sentences, chunk_size, overlap)
            # corpus.extend(chunks)
            for chunk in chunks:
                texts.append(chunk)
                corpus.append({
                    "text": chunk,
                    "category": category,
                    "source": source
                })
        
        return texts, corpus

    # Build BM25 index
    def build_bm25(self, texts: List[str]):
        tokenized_corpus = [word_tokenize(doc.lower()) for doc in texts]
        bm25 = BM25Okapi(tokenized_corpus)
        return bm25, texts, tokenized_corpus

    # Save BM25 index
    def save_bm25_index(self, doc_id: str, bm25, texts: List[str], corpus: List[Dict], save_dir: str = BM25_STORE):
            logging.info(f"Saving BM25 index for doc_id: {doc_id} at {save_dir}")
            os.makedirs(save_dir, exist_ok=True)
            logging.info(f"Ensured directory exists: {save_dir}")
           
            file_path = os.path.join(save_dir, f"bm25_index_{doc_id}.pkl")
            logging.info(f"BM25 index file path: {file_path}")
            data = {
                "bm25": bm25,
                "texts": texts,
                'corpus': corpus

            }
            logging.info(f"Prepared data for BM25 index with {len(texts)} texts and {len(corpus)} corpus entries")
            try:
                with open(file_path, "wb") as f:
                    logging.info(f"Opened file {file_path} for writing BM25 index")
                    pickle.dump(data, f)
                    logging.info(f"BM25 index data pickled successfully")
                logging.info(f"BM25 index saved to {file_path}")
            except Exception as e:
                logging.error(f"Failed to save BM25 index: {e}")


    async def index_pdf(self, folder_path: str, category: str, doc_id: str, user_id: str, tags: List[str], force_reindex: bool = False): 
 
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
                processed_pages = [page async for page in self.create_metadata(folder_path, category, tags,doc_id,user_id)]
                # You can now work with processed_pages here
                if not processed_pages:
                    raise ValueError(f"No pages were processed from {folder_path}")
                
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
            #configure model per user org settings
            config = await get_updated_app_config(organization_id)
            model_name = config.get("tags_model", "phi4-mini:3.8b")
            # Create chunks
            try:
                chunks = self.create_chunks(folder_path, tags, processed_pages, model_name)
                for i, doc in enumerate(chunks, start=1):
                    print(f"\n--- Chunk {i} ---")
                    print("ID:", doc.metadata.get("chunk_id", None))
                    print("Metadata:", doc.metadata)
                    print("Content:\n", doc.page_content)
                if not chunks:
                    raise ValueError(f"No chunks were created from {folder_path}")
                logging.info(f"Successfully created {len(chunks)} chunks")

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

            try:

                #Create BM25 corpus with smaller chunks
                texts, bm25_corpus = self.create_bm25_corpus(processed_pages, chunk_size=50, overlap=10)
                bm25, texts, tokenized_corpus = self.build_bm25(texts)
                self.save_bm25_index(doc_id, bm25, texts, bm25_corpus, save_dir=BM25_STORE)
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
                        break

            # 3️⃣ Include chunk if match found
            if meta_match or content_match:
                matched_chunks.append(doc)


        return matched_chunks



    async def ask_question(self, user_id: str, question: str, model_name: str = "gemma3:4b") -> dict:
        try:
            # === Step 1: Load Config & User Info ===

            existing_user = await organization_user_collection().find_one({"_id": ObjectId(user_id)})
            organization_id = existing_user.get("organization_id")
            config = await get_updated_app_config(organization_id)

            model_name = config.get("llm_model", model_name)
            embedding_model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            temperature = config.get("temperature", 0.7)
            query_model = config.get("query_model", "qwen3:8b")  # 'chroma', 'bm25', or 'hybrid'
            tags_model = config.get("tags_model", "phi4-mini:3.8b")
            category_id = existing_user.get("category_id", None)
            user_category = "unknown"
            if category_id:
                category_doc = await category_collection().find_one({"_id": ObjectId(category_id)})
                user_category = category_doc.get("name", "unknown") if category_doc else "unknown"
            
            print("=== User & Config Info ===")
            print("User ID:", user_id)
            print("Organization ID:", organization_id)
            print("Model Name:", model_name)
            print("Embedding Model:", embedding_model)
            print("Query Model:" ,query_model)
            print("Tags Model:", tags_model)
            print("Temperature:", temperature)
            print("User Category:", user_category)

            metadata_query_result = [w for w in word_tokenize(question.lower()) if w not in stop_words]

            # === Step 2: Chroma Retrieval ===
            vectorstore = Chroma(
                collection_name="rag-chroma",
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory,
            )

            try:
                retrieved_docs = vectorstore.max_marginal_relevance_search(
                    question,
                    k=10,
                    fetch_k=50,
                    lambda_mult=0.5,
                    filter={"category": user_category.strip().lower()},
                )
            except Exception as filter_error:
                logging.warning(f"MMR failed: {str(filter_error)}")
                retrieved_docs = vectorstore.similarity_search(
                            question,
                            k=10,
                            filter={"category": user_category.strip().lower()}
                       )

            filtered_chunks = self.filter_chunks_by_keywords(retrieved_docs, metadata_query_result)
            chroma_dicts = [convert_doc_to_dict(doc) for doc in filtered_chunks]

            # === Step 3: BM25 Retrieval ===
            bm25_dicts = run_bm25_keyword_search(metadata_query_result, user_category.strip().lower())
           

            # === Step 4: Rerank & Merge ===
            reranked_chroma = rerank_results(question, chroma_dicts, top_k=10)
            reranked_bm25 = rerank_results(question, bm25_dicts, top_k=10)

            combined_chunks = deduplicate_chunks(reranked_chroma + reranked_bm25)
            top_ranked_chunks = rerank_results(question, combined_chunks, top_k=10)
            # print("-------------------------------------------------------------------------------------------")
            # print("=== Reranked Chroma Chunks ===")
            # print("-------------------------------------------------------------------------------------------")
            # for i in reranked_chroma:
            #     print("Reranked Chroma:", i.get("rerank_score"), i.get("metadata"), i.get("text"))
            # print("-------------------------------------------------------------------------------------------")
            # print("=== Reranked BM25 ===")
            # print("-------------------------------------------------------------------------------------------")
            # for i in reranked_bm25:
            #     print("Reranked BM25:", i.get("rerank_score"), i.get("metadata", {}), i.get("text"))
            # print("-------------------------------------------------------------------------------------------")
            # print("=== Final Combined Chunks ===")
            # print("-------------------------------------------------------------------------------------------")
            # for i in top_ranked_chunks:
            #     print("Final:", i.get("rerank_score"), i.get("metadata", {}), i.get("text"))

            if not top_ranked_chunks:
                # return a clearer message or include a status field,
                # so the frontend can distinguish "no context" vs. final answer.
                return {"answer": "No relevant context found. Try broadening your query or re-ingesting documents.", "sources": [], "status": "no_context"}

            # === Step 5: Format Context ===
            context = "\n\n".join([format_chunk_for_context(chunk) for chunk in top_ranked_chunks])
            print("-------------------------------------------------------------------------------------------")
            print("=== Final Context for LLM ===")
            print("-------------------------------------------------------------------------------------------")
            print(context)

            # === Step 6: Query LLM ===
            prompt = f"""
            You must answer ONLY using information from the Context Chunks below.
            If a detail is not directly present in the provided context, reply:
            "Not enough information in the provided context."
            STRICT RULES:
            - Do NOT use prior knowledge
            - Do NOT guess or assume
            - Do NOT add features not explicitly stated in the context
            Context:
            {context}
            Question:
            {question}
            Your Answer:
            """

            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature},
                
            )

            # === Step 7: Return Answer & Sources ===
            result = {
                "answer": response.get("message", {}).get("content", "").strip(),
                "sources": [],
            }

            for chunk in top_ranked_chunks[:3]:
                metadata = chunk.get("metadata", {})
                source = str(metadata.get("source", "Unknown")).replace("\\", "/")
                result["sources"].append({
                    "file": source.split("/")[-1],
                    "content": chunk.get("text", ""),
                    "category": metadata.get("category", "unknown"),
                })

            return result

        except Exception as e:
            logging.error(f"Error in question answering: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "sources": [],
                "error": str(e),
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



def run_bm25_keyword_search(query: List[str], category: str, bm25_dir="./app/pipeline/bm25_store", top_n: int = 5) -> List[Dict]:
    """
    Performs BM25 keyword search across all saved indexes.
    Returns top-N dicts (with text + category metadata) strictly from the requested category.
    """
    results = []
    print(f"Running BM25 keyword search for query: {query}, category: {category}")

    if not os.path.isdir(bm25_dir):
        print(f"BM25 directory not found: {bm25_dir}")
        return []

    query_tokens = [q.lower() for q in query]

    for filename in os.listdir(bm25_dir):
        if not filename.endswith(".pkl"):
            continue

        file_path = os.path.join(bm25_dir, filename)
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                bm25 = data["bm25"]
                corpus = data["corpus"]  # [{text, category}, ...]

            # ✅ Strict filter by category
            filtered_corpus = [c for c in corpus if c["category"] == category]
            if not filtered_corpus:
                continue

            filtered_texts = [c["text"] for c in filtered_corpus]

            # Run BM25 on filtered texts
            top_results = bm25.get_top_n(query_tokens, filtered_texts, n=top_n)

            # Convert back into dicts (with category and source preserved)
            for t in top_results:
                # Find the corpus entry for this text
                match = next((c for c in filtered_corpus if c["text"] == t), None)
                source = match.get("source", "unknown") if match else "unknown"
                results.append({"text": t, "metadata": {"category": category, "source": source}})

        except Exception as e:
            print(f"Failed to process BM25 index for {filename}: {e}")

    return results

def convert_doc_to_dict(doc):
    return {
        "text": doc.page_content,
        "metadata": doc.metadata,
        "chunk_id": doc.metadata.get("chunk_id", None),
        "score": None,
    }

import hashlib

def deduplicate_chunks(chunks: List[Dict]) -> List[Dict]:
    seen_hashes = set()
    unique = []
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        hash_val = hashlib.md5(text.encode("utf-8")).hexdigest()
        if hash_val not in seen_hashes:
            seen_hashes.add(hash_val)
            unique.append(chunk)
    return unique

def format_chunk_for_context(chunk: dict) -> str:
    metadata = chunk.get("metadata", {})
    chunk_id = chunk.get("chunk_id", "N/A")
    source = metadata.get("source", "Unknown")
    title = metadata.get("title", "")
    section = metadata.get("section_num", "")
    file_meta = metadata.get("file_metadata", "")

    return (
        # f"[Chunk ID: {chunk_id} | Source: {source} | Title: {title} | Section: {section}]\n"
        f"File Metadata: {metadata}\n"
        f"Content:\n{chunk.get('text', '')}"
    )




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
    # import asyncio
    
    # async def main():
        # await ensure_models_available()
        interactive_qa()
    
    # asyncio.run(main())

async def ensure_models_available():
    """Check and download required models for offline use."""
    models_to_check = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ]
    
    for model_name in models_to_check:
        cache_dir = f"./models/{model_name.split('/')[-1]}"
        if not os.path.exists(cache_dir):
            print(f"Downloading {model_name} for offline use...")
            if "cross-encoder" in model_name:
                CrossEncoder(model_name, cache_folder=cache_dir)
            else:
                SentenceTransformer(model_name, cache_folder=cache_dir)
    
    print("All required models are available for offline use")

async def main():
    """Initialize PDFProcessor and required components."""
    try:
        await connect_to_mongodb()
        await ensure_models_available()
        global processor
        processor = PDFProcessor()
        # Initialize ChromaDB and other components if needed
        logging.info("PDFProcessor initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing PDFProcessor: {e}")
        raise