import sys
import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document, BaseRetriever
from langchain.embeddings.base import Embeddings
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from config import get_env_var

try:
    from google.cloud import firestore
    from google.auth import default
    import google.auth.exceptions
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logging.warning("Google Cloud Firestore not available. Install google-cloud-firestore to use Firestore storage.")


class FirestoreVectorStore:
    """Firestore-based vector store for similarity search"""
    
    def __init__(self, firestore_loader: 'FirestoreDataLoader', embeddings: Embeddings):
        self.firestore_loader = firestore_loader
        self.embeddings = embeddings
        self.collection_name = firestore_loader.collection_name + "_vectors"
        self.vector_collection = firestore_loader.db.collection(self.collection_name)
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents with their embeddings to Firestore"""
        from google.cloud import firestore
        try:
            batch = self.firestore_loader.db.batch()
            
            # Generate embeddings for all documents
            texts = [doc.page_content for doc in documents]
            embeddings_list = self.embeddings.embed_documents(texts)
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings_list)):
                doc_ref = self.vector_collection.document(f"doc_{i}_{hash(doc.page_content)}")
                doc_data = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "embedding": embedding,  # Store as array
                    "doc_id": f"doc_{i}",
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                batch.set(doc_ref, doc_data)
            
            batch.commit()
            logging.info(f"Saved {len(documents)} documents with embeddings to Firestore collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Failed to save documents with embeddings to Firestore: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search using cosine similarity"""
        try:
            # Get query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Get all documents with embeddings
            docs = []
            similarities = []
            
            for doc in self.vector_collection.stream():
                doc_data = doc.to_dict()
                stored_embedding = doc_data.get("embedding", [])
                
                if stored_embedding:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    similarities.append(similarity)
                    
                    document = Document(
                        page_content=doc_data.get("content", ""),
                        metadata=doc_data.get("metadata", {})
                    )
                    docs.append(document)
            
            # Sort by similarity and return top k
            if docs:
                doc_similarities = list(zip(docs, similarities))
                doc_similarities.sort(key=lambda x: x[1], reverse=True)
                return [doc for doc, _ in doc_similarities[:k]]
            
            return []
        except Exception as e:
            logging.error(f"Failed to perform similarity search: {str(e)}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Perform similarity search and return documents with similarity scores"""
        try:
            # Get query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Get all documents with embeddings
            docs = []
            similarities = []
            
            for doc in self.vector_collection.stream():
                doc_data = doc.to_dict()
                stored_embedding = doc_data.get("embedding", [])
                
                if stored_embedding:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    similarities.append(similarity)
                    
                    document = Document(
                        page_content=doc_data.get("content", ""),
                        metadata=doc_data.get("metadata", {})
                    )
                    docs.append(document)
            
            # Sort by similarity and return top k with scores
            if docs:
                doc_similarities = list(zip(docs, similarities))
                doc_similarities.sort(key=lambda x: x[1], reverse=True)
                return doc_similarities[:k]
            
            return []
        except Exception as e:
            logging.error(f"Failed to perform similarity search with score: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logging.error(f"Failed to calculate cosine similarity: {str(e)}")
            return 0.0
    
    def get_document_count(self) -> int:
        """Get the number of documents in the vector collection"""
        try:
            docs = list(self.vector_collection.stream())
            return len(docs)
        except Exception as e:
            logging.error(f"Failed to get vector document count from Firestore: {str(e)}")
            return 0
    
    def delete_all_vectors(self) -> None:
        """Delete all vectors from the collection"""
        try:
            batch = self.firestore_loader.db.batch()
            docs = self.vector_collection.stream()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Firestore batch has a limit of 500 operations
                if count % 500 == 0:
                    batch.commit()
                    batch = self.firestore_loader.db.batch()
            
            if count % 500 != 0:
                batch.commit()
                
            logging.info(f"Deleted {count} vector documents from Firestore collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Failed to delete vector documents from Firestore: {str(e)}")
            raise
    
    def as_retriever(self, **kwargs):
        """Return a retriever interface for this vector store"""
        
        class FirestoreRetriever(BaseRetriever):
            """Retriever wrapper for FirestoreVectorStore that inherits from BaseRetriever"""
            
            vector_store: 'FirestoreVectorStore'
            k: int = 4
            search_type: str = 'similarity'
            score_threshold: float = 0.5
            
            def __init__(self, vector_store: 'FirestoreVectorStore', **kwargs):
                super().__init__(
                    vector_store=vector_store,
                    k=kwargs.get('k', 4),
                    search_type=kwargs.get('search_type', 'similarity'),
                    score_threshold=kwargs.get('score_threshold', 0.5)
                )
            
            def _get_relevant_documents(
                self, query: str, *, run_manager: CallbackManagerForRetrieverRun
            ) -> List[Document]:
                """Get relevant documents for a query."""
                if self.search_type == "similarity":
                    return self.vector_store.similarity_search(query, k=self.k)
                elif self.search_type == "similarity_score_threshold":
                    docs_and_scores = self.vector_store.similarity_search_with_score(query, k=self.k)
                    return [doc for doc, score in docs_and_scores if score >= self.score_threshold]
                else:
                    return self.vector_store.similarity_search(query, k=self.k)
        
        return FirestoreRetriever(self, **kwargs)
    

class FirestoreDataLoader:
    """Handle Firestore operations for document storage and retrieval"""
    
    def __init__(self):
        if not FIRESTORE_AVAILABLE:
            raise ImportError("Google Cloud Firestore is not available. Please install google-cloud-firestore.")
        
        from google.cloud import firestore
        
        self.project_id = get_env_var("GCP_PROJECT_ID")
        self.database_name = get_env_var("FIRESTORE_DATABASE", "(default)")
        self.collection_name = get_env_var("FIRESTORE_COLLECTION", "documents")
        self.credentials_path = get_env_var("FIRESTORE_CREDENTIALS_PATH")
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        # Initialize Firestore client
        try:
            if self.credentials_path:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
            
            # Use named database if specified, otherwise use default
            if self.database_name and self.database_name != "(default)":
                self.db = firestore.Client(project=self.project_id, database=self.database_name)
                logging.info(f"Initialized Firestore client for project: {self.project_id}, database: {self.database_name}")
            else:
                self.db = firestore.Client(project=self.project_id)
                logging.info(f"Initialized Firestore client for project: {self.project_id}, database: (default)")
                
            self.collection = self.db.collection(self.collection_name)
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {str(e)}")
            raise
    
    def create_vector_store(self, embeddings: Embeddings) -> FirestoreVectorStore:
        """Create a FirestoreVectorStore instance"""
        return FirestoreVectorStore(self, embeddings)
    
    def save_documents(self, documents: List[Document]) -> None:
        """Save documents to Firestore"""
        from google.cloud import firestore
        try:
            batch = self.db.batch()
            
            for i, doc in enumerate(documents):
                doc_ref = self.collection.document(f"doc_{i}_{hash(doc.page_content)}")
                doc_data = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "doc_id": f"doc_{i}",
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                batch.set(doc_ref, doc_data)
            
            batch.commit()
            logging.info(f"Saved {len(documents)} documents to Firestore collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Failed to save documents to Firestore: {str(e)}")
            raise
    
    def load_documents(self) -> List[Document]:
        """Load documents from Firestore"""
        try:
            docs = []
            for doc in self.collection.stream():
                doc_data = doc.to_dict()
                document = Document(
                    page_content=doc_data.get("content", ""),
                    metadata=doc_data.get("metadata", {})
                )
                docs.append(document)
            
            logging.info(f"Loaded {len(docs)} documents from Firestore collection: {self.collection_name}")
            return docs
        except Exception as e:
            logging.error(f"Failed to load documents from Firestore: {str(e)}")
            raise
    
    def delete_all_documents(self) -> None:
        """Delete all documents from the collection"""
        try:
            batch = self.db.batch()
            docs = self.collection.stream()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Firestore batch has a limit of 500 operations
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if count % 500 != 0:
                batch.commit()
                
            logging.info(f"Deleted {count} documents from Firestore collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Failed to delete documents from Firestore: {str(e)}")
            raise
    
    def get_document_count(self) -> int:
        """Get the number of documents in the collection"""
        try:
            docs = list(self.collection.stream())
            return len(docs)
        except Exception as e:
            logging.error(f"Failed to get document count from Firestore: {str(e)}")
            return 0
    
    def check_connection(self) -> bool:
        """Check if Firestore connection is working"""
        try:
            # Try to access the collection
            list(self.collection.limit(1).stream())
            return True
        except Exception as e:
            logging.error(f"Firestore connection check failed: {str(e)}")
            return False
