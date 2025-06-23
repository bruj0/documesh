import sys
import logging

sys.path.append('../')
sys.path.append('./')

from langchain.document_loaders import ConfluenceLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
import os
from time import sleep

try:
    from firestore_db import FirestoreDataLoader
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logging.warning("Firestore support not available. Install google-cloud-firestore to use Firestore storage.")

class DataLoader():
    """Create, load, save the DB using the confluence Loader"""
    def __init__(self, storage_type="firestore"):
        """
        Initialize DataLoader with Firestore storage
        
        Args:
            storage_type (str): Only 'firestore' is supported
        """
        if storage_type != "firestore":
            raise ValueError("Only 'firestore' storage type is supported")
            
        self.storage_type = storage_type
        self.confluence_url = os.environ.get("CONFLUENCE_SPACE_NAME")
        self.username = os.environ.get("EMAIL_ADRESS")
        self.api_key = os.environ.get("CONFLUENCE_PRIVATE_API_KEY")
        self.space_key = os.environ.get("CONFLUENCE_SPACE_KEY")
        self.persist_directory = os.environ.get("PERSIST_DIRECTORY")
        
        # Initialize Firestore loader
        if not FIRESTORE_AVAILABLE:
            raise ImportError("Firestore storage requested but google-cloud-firestore is not available")
        self.firestore_loader = FirestoreDataLoader()
        logging.info("Initialized with Firestore storage backend")

    def load_from_confluence_loader(self):
        """Load HTML files from Confluence"""
        print(f"Loading from Confluence space: {self.space_key}")
        print(f"Confluence URL: {self.confluence_url}")
        print(f"Confluence username: {self.username}")
        print(f"Confluence space key: {self.space_key}")
        print(f"Persist directory: {self.persist_directory}")
        print("Loading documents from Confluence...")
        loader = ConfluenceLoader(
            url=self.confluence_url,
            username=self.username,
            api_key=self.api_key
        )

        docs = loader.load(
            space_key=self.space_key,
            # include_attachments=True,
            )
        
        return docs
    

    def split_docs(self, docs):
        # Markdown
        headers_to_split_on = [
            ("#", "Title 1"),
            ("##", "Sub-title 1"),
            ("###", "Sub-title 2"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

        # Split based on markdown and add original metadata
        md_docs = []
        for doc in docs:
            md_doc = markdown_splitter.split_text(doc.page_content)
            for i in range(len(md_doc)):
                md_doc[i].metadata = md_doc[i].metadata | doc.metadata
            md_docs.extend(md_doc)

        # RecursiveTextSplitter
        # Chunk size big enough
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=20,
            separators=["\n\n", "\n", "(?<=\. )", " ", ""]
        )

        splitted_docs = splitter.split_documents(md_docs)
        return splitted_docs

    def save_to_db(self, splitted_docs):
        """Save chunks to Firestore DB"""
        return self.save_to_firestore(splitted_docs)
    
    def save_to_firestore(self, splitted_docs):
        """Save documents with vectors to Firestore"""
        embeddings = HuggingFaceEmbeddings()
        
        # Create Firestore vector store
        vector_store = self.firestore_loader.create_vector_store(embeddings)
        
        # Add documents with embeddings to Firestore
        vector_store.add_documents(splitted_docs)
        
        return vector_store 

    def load_from_db(self):
        """Load chunks from Firestore DB"""
        return self.load_from_firestore()
    
    def load_from_firestore(self):
        """Load from Firestore vector store"""
        embeddings = HuggingFaceEmbeddings()
        
        # Create Firestore vector store
        vector_store = self.firestore_loader.create_vector_store(embeddings)
        
        return vector_store

    def set_db(self, reset=False):
        """Create, save, and load db"""
        if reset:
            logging.info("Resetting the database...")
            # Clear Firestore collection
            self.firestore_loader.delete_all_documents()
            # Also delete vectors
            embeddings = HuggingFaceEmbeddings()
            vector_store = self.firestore_loader.create_vector_store(embeddings)
            vector_store.delete_all_vectors()
        else:
            logging.info("Creating or loading the database...")

        # Load docs
        docs = self.load_from_confluence_loader()

        # Split Docs
        splitted_docs = self.split_docs(docs)

        # Save to DB
        db = self.save_to_db(splitted_docs)

        return db

    def get_db(self):
        """Create, save, and load db"""
        db = self.load_from_db()
        return db



if __name__ == "__main__":
    pass
