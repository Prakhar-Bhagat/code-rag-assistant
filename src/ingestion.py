import sqlite3
import hashlib
import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from .parser import load_codebase


class IngestionPipeline:

    def __init__(self, db_path="./db"):
        # Ensure your Ollama is running and you have run: ollama pull nomic-embed-text
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.db_path = db_path
        
        # Ensure the DB directory exists before creating the SQLite file
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize SQLite for file deduplication
        self.conn = sqlite3.connect(os.path.join(self.db_path, "file_hashes.db"), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Creates the tracking table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT
            )
        ''')
        self.conn.commit()

    def _get_content_hash(self, content: str) -> str:
        """Generates a SHA-256 hash of the file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def filter_unmodified_files(self, docs):
        """Returns only documents that are new or have been modified."""
        cursor = self.conn.cursor()
        new_or_modified_docs = []

        for doc in docs:
            file_path = doc.metadata.get('source', 'unknown')
            content_hash = self._get_content_hash(doc.page_content)

            # Check if file exists in DB and if its hash matches
            cursor.execute('SELECT file_hash FROM file_hashes WHERE file_path = ?', (file_path,))
            result = cursor.fetchone()

            if result and result[0] == content_hash:
                continue # Skip this file, it hasn't changed!

            # If we get here, it's a new file or the content changed
            new_or_modified_docs.append(doc)

            # Update the database with the new hash
            cursor.execute('''
                REPLACE INTO file_hashes (file_path, file_hash)
                VALUES (?, ?)
            ''', (file_path, content_hash))

        self.conn.commit()
        return new_or_modified_docs

    def process_directory(self, path):
        # Resolve absolute path to be safe on Mac
        absolute_path = os.path.abspath(path)
        if not os.path.exists(absolute_path):
            print(f"Error: Path {absolute_path} does not exist.")
            return

        print(f"--- Loading code from {absolute_path} ---")
        raw_code_docs = load_codebase(absolute_path)
        if not raw_code_docs:
            print("No documents found! Check if .py files are in the folder.")
            return

        # NEW: Filter out files we've already ingested
        new_docs = self.filter_unmodified_files(raw_code_docs)

        if not new_docs:
            print("--- No new or modified files detected. Skipping embedding! ---")
            return self.get_retriever()

        print(f"--- Processing {len(new_docs)} NEW/MODIFIED files. Splitting into chunks... ---")
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=400, chunk_overlap=50
        )
        # Make sure to split the filtered new_docs, not the raw_code_docs
        texts = python_splitter.split_documents(new_docs)

        print(f"--- Embedding {len(texts)} chunks into ChromaDB at {self.db_path} ---")
        vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.db_path,
            collection_metadata={"hnsw:space": "cosine"}
        )
        print("--- Ingestion Complete ---")
        return vectorstore

    def get_retriever(self):
        vectorstore = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings,
            collection_metadata={"hnsw:space": "cosine"}
        )
        return vectorstore.as_retriever(
            search_type="similarity",  # Keeping your similarity setting
            search_kwargs={"k": 4}     # Keeping your k=4 setting
        )

    def unzip_repo(self, zip_path, extract_to):
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"--- Unzipped {zip_path} to {extract_to} ---")

    def get_scores(self, query: str):
        vectorstore = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings,
            collection_metadata={"hnsw:space": "cosine"} # Added to match your DB config
        )
        results = vectorstore.similarity_search_with_score(query, k=4)
        return [(doc.metadata.get("source"), score) for doc, score in results]

if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.process_directory("./test_repo")