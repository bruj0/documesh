import sys
import load_db
import collections
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_google_vertexai import VertexAI
import json
from config import get_env_var


class HelpDesk():
    """Create the necessary objects to create a QARetrieval chain"""
    def __init__(self, new_db=True, storage_type="firestore"):
        """
        Initialize the HelpDesk object.
        
        Args:
            new_db (bool): Whether to create a new database or use an existing one.
            storage_type (str): Storage type - only 'firestore' is supported
        """
        if storage_type != "firestore":
            raise ValueError("Only 'firestore' storage type is supported")
        
        self.new_db = new_db
        self.storage_type = storage_type
        self.template = self.get_template()
        self.llm = self.get_llm()
        self.prompt = self.get_prompt()

        # Create data loader with storage type
        self.data_loader = load_db.DataLoader(storage_type=storage_type)

        if self.new_db: 
            self.db = self.data_loader.set_db(reset=False)
        else:
            self.db = self.data_loader.get_db()

        self.retriever = self.db.as_retriever()


    def get_template(self):
        template = """
        Given this text extracts:
        -----
        {context}
        -----
        Please answer with to the following question:
        Question: {input}
        Helpful Answer:

        If the context is not related to the question, please answer "I don't know".
        """
        return template

    def get_prompt(self) -> PromptTemplate:
        prompt = PromptTemplate(
            template=self.template,
            input_variables=["context", "input"]
        )
        return prompt

    def get_llm(self):
        """
        Returns the VertexAI LLM with Gemini model
        """
        # Initialize VertexAI with Gemini model
        llm = VertexAI(
            model_name="gemini-2.5-flash",
            temperature=0.7,
            project=get_env_var("GCP_PROJECT_ID"),
            location=get_env_var("GCP_LOCATION", "us-central1"),
        )
        
        return llm

    def retrieval_qa_inference(self, question, verbose=True):
        query = {"input": question}
        #answer = self.retrieval_qa_chain(query)
        combine_docs_chain = create_stuff_documents_chain(self.llm, self.prompt)

        chain =  self.prompt | self.llm 
        chain = create_retrieval_chain(self.retriever, combine_docs_chain)

    # Use .stream() for streaming output if available

        for chunk in chain.stream(query):
            chunk = dict(chunk)
            yield chunk.get("answer", "")


        retrieved_docs = self.retriever.invoke(question)#.get("context")
        sources_str = self.list_top_k_sources(retrieved_docs, k=2)
        yield sources_str

    def list_top_k_sources(self, answer, k=2):
        sources = [
            f'[{res.metadata["title"]}]({res.metadata["source"]})'
            for res in answer
        ]

        distinct_sources = []
        distinct_sources_str = ""
        
        if sources:
            k = min(k, len(sources))
            distinct_sources = list(zip(*collections.Counter(sources).most_common()))[0][:k]
            distinct_sources_str = "  \n- ".join(distinct_sources)

        if len(distinct_sources) == 1:
            return f"\n \n This might be useful to you:  \n- {distinct_sources_str}"

        elif len(distinct_sources) > 1:
            return f"\n \n Here are {len(distinct_sources)} sources that might be useful to you:  \n- {distinct_sources_str}"

        else:
            return "\n \n Sorry, I couldn't find any resources to answer your question."
