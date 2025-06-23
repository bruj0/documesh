# Streamlit
# Basic example with a improvementd:
# Add streaming
# Add Conversation history
# Optimize Splitter, Retriever,
import streamlit as st
from help_desk import HelpDesk
from config import set_env, get_env

#async def streaming_answer(model: HelpDesk, prompt: str):
#    async for chunk in model.retrieval_qa_inference(prompt):
#        # print(json.dumps({"answer": chunk}))
#        yield chunk


def get_model(backend_type="firestore"):
    """
    Initialize and cache the model.
    
    Args:
        backend_type (str): Storage backend to use (only 'firestore' is supported)
    
    Returns:
        HelpDesk: An initialized HelpDesk object using VertexAI.
    """
    if backend_type != "firestore":
        raise ValueError("Only 'firestore' storage backend is supported")
    model = HelpDesk(new_db=False, storage_type=backend_type)
    return model

def chat_page():
    # App title
    st.title("Document Management System")

    # Display 
    # Set the initial environment to the first one in the dictionary if not already set
    if "current_env" not in st.session_state:
        print("Setting initial environment")
        initial_env =  get_env()
        print(f"Initial environment: {initial_env}")
        st.session_state["current_env"] = initial_env

    # Initialize model with current storage type
    st.session_state["model"] = get_model(backend_type="firestore")
    
    model = st.session_state["model"]

    # Streamlit
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])


    if prompt := st.chat_input("How can I help you?"):
        # Add prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Get answer

        answer = ""

        with st.chat_message("assistant"):
            placeholder = st.empty()
           # placeholder.write(result)
            for chunk in model.retrieval_qa_inference(prompt):
                if chunk:
                    answer += chunk
                    placeholder.write(answer)  # Update the answer progressively

        st.session_state.messages.append({"role": "assistant", "content": answer + '  \n  \n'})




chat_page()
