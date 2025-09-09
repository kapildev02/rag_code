import re
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

    def create_metadata(self, folder_path: str, category: str, force_reprocess: bool = True) -> Iterator[Dict]:
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

        page_data = {
            'section_num': i+1,
            'category': category,
            'title': title,
            'text': batch,
            'summary': summary,
            'source': str(md_files),
            'format': 'markdown',
            'tables': tables,
        }

        pages.append(page_data)  # Store for caching
        yield page_data  # Yield processed data immediately
        # Cache processed pages
        self.processed_files[folder_path] = pages

    def _extract_section_title(self, markdown_content: str) -> Optional[str]:
        prompt = f"""Extract the main title from the following Markdown content. 
        If there is no clear title, return the best possible inferred title.\n\n
        {markdown_content}\n\nTitle:"""
        
        response = ollama.chat(model="gemma3:1b", messages=[{"role": "user", "content": prompt}])
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
            
        return tables
        
    def summarize_page(self,content: str, is_markdown: bool = True, model_name: str = "gemma3:1b") -> str:
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

            return summary

        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            return "Summary generation failed. Please check the content and try again."
        
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

    async def index_pdf(self, folder_path: str, category: str, doc_id: str, user_id: str, force_reindex: bool = False): 
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

                processed_pages = list(self.create_metadata(folder_path, category))
                if not processed_pages:
                    raise ValueError(f"No pages were processed from {folder_path}")
                logging.info(f"Extracted metadata: {processed_pages}")
                logging.info(f"Successfully extracted metadata from {len(processed_pages)} pages")
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

   

    async def ask_question(self, user_id: str, question: str, model_name: str = "gemma2:2b") -> dict:
        try:
            # Get organization admin app config to fetch organization-specific config
            print("Fetching organization user for user_id:", user_id)

            from app.db.mongodb import organization_user_collection
            existing_user=await organization_user_collection().find_one({"_id": ObjectId(user_id)})

            organization_id = existing_user.get("organization_id")
            print("Fetching organization users for organization_id:", organization_id)

            config = await get_updated_app_config(organization_id)

            model_name = config['llm_model'] if "llm_model" in config else "gemma3:1b"
            embedding_model = config['embedding_model'] if "embedding_model" in config else "sentence-transformers/all-MiniLM-L6-v2"
            temperature = config['temperature'] if "temperature" in config else 0.7

            category_id = existing_user.get("category_id", None)
            user_category = "unknown"
            if category_id:
                from app.db.mongodb import category_collection
                category_doc = await category_collection().find_one({"_id": ObjectId(category_id)})
                if category_doc:
                    user_category = category_doc.get("name", "unknown")

            logging.info(f"Category ID: {category_id}, User Category: {user_category}")
            logging.info(f"Using model: {model_name}, temperature: {temperature}")
            
           
            # Set model name
            self.llm_model_name = model_name
            
            # Get relevant documents from vector store
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

            if not retrieved_docs:
                return {
                    "answer": "I couldn't find any relevant information to answer your question in the available documents.",
                    "sources": []
                }

            # Build context with better error handling
            try:
                context_parts = []
                for doc in retrieved_docs:
                    if doc and hasattr(doc, 'page_content'):
                        context_parts.append(doc.page_content)
                context = "\n\n".join(context_parts) if context_parts else ""
            except Exception as context_error:
                logging.error(f"Error building context: {str(context_error)}")
                context = ""

            if not context:
                return {
                    "answer": "Sorry, I encountered an issue processing the relevant documents.",
                    "sources": []
                }

            # Create prompt with context
            prompt = f"""
            Answer the question based on the following context:
            
            Context:
            {context}
            
            Question: {question}
            
            Give a comprehensive answer based only on the provided context. If the context doesn't contain the answer, state that you don't have enough information.
            """
            
            # Get response using Ollama
            response = ollama.chat(
                model=self.llm_model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature}
            )
            
        
        #     # Format the response
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