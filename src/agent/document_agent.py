"""
Document agent module for technical document management system.
"""
import os
from typing import Dict, List, Any, Optional

# Import Google ADK components
from google.adk.agents import Agent
from google.adk.tools import Tool

# Import local modules
from ..search import similarity

# Configure environment
PROJECT_ID = os.environ.get("PROJECT_ID", "your-project-id")
LOCATION = os.environ.get("LOCATION", "us-central1")

class DocumentSearchAgent:
    """Agent for document search and information extraction using Google ADK."""
    
    def __init__(self):
        """Initialize the document search agent."""
        # Define custom tools
        self.search_tool = Tool(
            name="search_documents",
            description="Search for technical documents by text query",
            function=self._search_documents
        )
        
        self.similar_docs_tool = Tool(
            name="find_similar_documents",
            description="Find documents similar to a specified document",
            function=self._find_similar_documents
        )
        
        self.extract_info_tool = Tool(
            name="extract_document_information",
            description="Extract specific information from a document",
            function=self._extract_information
        )
        
        self.summarize_tool = Tool(
            name="summarize_document",
            description="Generate a summary of a document",
            function=self._summarize_document
        )
        
        # Initialize the agent with tools
        self.agent = Agent(
            name="technical_document_assistant",
            model="gemini-2.0-flash",
            description="An AI assistant specialized in technical document management",
            instruction="""
            You are a technical document assistant that helps users find and analyze 
            technical documents. You can search for documents, find similar documents,
            extract information, and generate summaries.
            
            When responding to queries about documents:
            1. Be precise and technical in your responses
            2. Provide document IDs and titles when referring to documents
            3. Offer to perform additional analysis when appropriate
            4. When dealing with technical diagrams, mention their presence
            """,
            tools=[
                self.search_tool,
                self.similar_docs_tool,
                self.extract_info_tool,
                self.summarize_tool
            ]
        )
    
    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language query using the agent.
        
        Args:
            query: The user's natural language query
            session_id: Optional session ID for continuous conversations
            context: Optional context information
            
        Returns:
            Response dictionary with agent's answer and related documents
        """
        # Process the query with the agent
        response = self.agent.chat(
            query,
            session_id=session_id,
            context=context or {}
        )
        
        # Format response
        result = {
            "response": response.text,
            "documents": [],
            "thinking": None
        }
        
        # Extract any document references from the response
        # This is a simple approach - in production you would use more sophisticated parsing
        if hasattr(response, "documents") and response.documents:
            result["documents"] = response.documents
        
        # Include reasoning if available
        if hasattr(response, "thinking") and response.thinking:
            result["thinking"] = response.thinking
            
        return result
    
    def find_similar_documents(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to the given query.
        
        Args:
            query: Text query to find similar documents
            top_k: Maximum number of results to return
            
        Returns:
            List of similar documents
        """
        # Generate embedding for query
        from ..ingestion import embedding
        query_embedding = embedding.generate_text_embedding(query)
        
        # Search for similar documents
        results = similarity.search_text_similarity(
            query_embedding,
            top_k=top_k
        )
        
        return results
    
    def extract_information(
        self,
        document_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract specific information from a document.
        
        Args:
            document_id: ID of the document
            fields: Optional list of fields to extract
            
        Returns:
            Dictionary of extracted information
        """
        # Get document content from Firestore
        from google.cloud import firestore
        db = firestore.Client()
        
        doc_ref = db.collection("documents").document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Document {document_id} not found")
            
        doc_data = doc.to_dict()
        text_content = doc_data.get("text_content", "")
        
        # Use Vertex AI to extract information
        # This is a simplified implementation
        # In production, use more sophisticated extraction techniques
        extracted_info = self._extract_with_llm(text_content, fields)
        
        return extracted_info
    
    def summarize_document(
        self,
        document_id: str,
        max_length: int = 500
    ) -> str:
        """
        Generate a summary of a document.
        
        Args:
            document_id: ID of the document
            max_length: Maximum length of the summary
            
        Returns:
            Document summary
        """
        # Get document content from Firestore
        from google.cloud import firestore
        db = firestore.Client()
        
        doc_ref = db.collection("documents").document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Document {document_id} not found")
            
        doc_data = doc.to_dict()
        text_content = doc_data.get("text_content", "")
        
        # Use Vertex AI to generate summary
        # This is a simplified implementation
        # In production, use more sophisticated summarization techniques
        summary = self._summarize_with_llm(text_content, max_length)
        
        return summary
    
    def compare_documents(
        self,
        document_ids: List[str],
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple documents.
        
        Args:
            document_ids: List of document IDs to compare
            aspects: Optional list of aspects to focus on
            
        Returns:
            Comparison results
        """
        if len(document_ids) < 2:
            raise ValueError("At least 2 documents required for comparison")
        
        # Get document content from Firestore
        from google.cloud import firestore
        db = firestore.Client()
        
        documents = []
        for doc_id in document_ids:
            doc_ref = db.collection("documents").document(doc_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Document {doc_id} not found")
                
            doc_data = doc.to_dict()
            documents.append({
                "id": doc_id,
                "title": doc_data.get("filename", ""),
                "content": doc_data.get("text_content", "")
            })
        
        # Use Vertex AI to compare documents
        comparison = self._compare_with_llm(documents, aspects)
        
        return comparison
    
    # Private helper methods for the tools
    def _search_documents(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Internal implementation of document search tool."""
        results = self.find_similar_documents(query, top_k=limit)
        return {"results": results, "count": len(results)}
    
    def _find_similar_documents(self, document_id: str, limit: int = 5) -> Dict[str, Any]:
        """Internal implementation of similar document finder tool."""
        results = similarity.find_similar_documents(document_id=document_id, top_k=limit)
        return {"results": results, "count": len(results)}
    
    def _extract_information(self, document_id: str, fields: List[str]) -> Dict[str, Any]:
        """Internal implementation of information extraction tool."""
        return self.extract_information(document_id, fields)
    
    def _summarize_document(self, document_id: str, max_length: int = 500) -> Dict[str, Any]:
        """Internal implementation of document summarization tool."""
        summary = self.summarize_document(document_id, max_length)
        return {"summary": summary}
    
    # LLM helper methods
    def _extract_with_llm(self, text_content: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract information from text content using an LLM.
        
        In a production system, this would use Vertex AI with proper prompting
        for information extraction. This is a placeholder implementation.
        """
        # Simplified placeholder implementation
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Initialize Vertex AI with project and location
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Load the model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Create prompt for extraction
        field_str = ", ".join(fields) if fields else "key information"
        prompt = f"""
        Extract the following information from the technical document:
        {field_str}
        
        Document content:
        {text_content[:10000]}  # Truncate for simplicity
        
        Format the output as a JSON object with the fields as keys.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Parse response - in production, add proper error handling and parsing
        try:
            import json
            # Attempt to extract JSON from response
            text = response.text
            # Find JSON block in the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            
            # Fallback to simple key-value extraction if JSON parsing fails
            extracted_info = {}
            if fields:
                for field in fields:
                    # Simple extraction logic - look for field name followed by information
                    field_pattern = f"{field}:"
                    if field_pattern in text:
                        start = text.index(field_pattern) + len(field_pattern)
                        end = text.find("\n", start)
                        if end == -1:
                            end = len(text)
                        extracted_info[field] = text[start:end].strip()
            
            return extracted_info
            
        except Exception as e:
            print(f"Error parsing extraction response: {str(e)}")
            return {"error": "Failed to parse extraction results"}
            
    def _summarize_with_llm(self, text_content: str, max_length: int = 500) -> str:
        """
        Summarize text content using an LLM.
        
        In a production system, this would use Vertex AI with proper prompting
        for summarization. This is a placeholder implementation.
        """
        # Simplified placeholder implementation
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Initialize Vertex AI with project and location
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Load the model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Create prompt for summarization
        prompt = f"""
        Summarize the following technical document in approximately {max_length} characters:
        
        {text_content[:20000]}  # Truncate for simplicity
        
        The summary should capture the main technical details and key points.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return summarized text
        return response.text
    
    def _compare_with_llm(
        self,
        documents: List[Dict[str, Any]],
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare documents using an LLM.
        
        In a production system, this would use Vertex AI with proper prompting
        for document comparison. This is a placeholder implementation.
        """
        # Simplified placeholder implementation
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Initialize Vertex AI with project and location
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Load the model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Create document excerpts (truncated)
        doc_excerpts = []
        for doc in documents:
            title = doc.get("title", f"Document {doc.get('id')}")
            content = doc.get("content", "")[:5000]  # Truncate for simplicity
            doc_excerpts.append(f"--- {title} ---\n{content}\n")
        
        # Create aspects string if provided
        aspects_str = ""
        if aspects and len(aspects) > 0:
            aspects_str = "Focus on comparing these aspects: " + ", ".join(aspects)
        
        # Create prompt for comparison
        prompt = f"""
        Compare the following technical documents:
        
        {"\n\n".join(doc_excerpts)}
        
        {aspects_str}
        
        Format the comparison as:
        1. Key similarities
        2. Key differences
        3. Individual strengths
        4. Overall analysis
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return comparison text
        return {
            "comparison": response.text,
            "documents": [doc.get("title", doc.get("id")) for doc in documents]
        }


# Create a singleton instance
agent = DocumentSearchAgent()
