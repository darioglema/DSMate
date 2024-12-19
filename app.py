import streamlit as st
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredHTMLLoader,
)
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
import os
from typing import List, Dict
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import logging
from pathlib import Path

# ---- Function Definitions ----
@st.cache_resource(show_spinner=False)
def get_supported_files_in_directory(directory: str, extensions: List[str] = [".pdf", ".txt", ".docx", ".pptx", ".html"]) -> List[str]:
    """
    Get a list of supported files in the specified directory and its subdirectories.
    """
    supported_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                supported_files.append(os.path.join(root, file))
    return supported_files

@st.cache_resource(show_spinner=False)
def initialize_retrievers(directory: str) -> Dict[str, Chroma]:
    """
    Initialize a retriever for each document in the directory.
    """
    files = get_supported_files_in_directory(directory)
    
    if not files:
        raise ValueError("No supported files found in the directory.")

    retrievers = {}
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".docx": UnstructuredWordDocumentLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".html": UnstructuredHTMLLoader,
    }

    for file_path in files:
        extension = os.path.splitext(file_path)[-1].lower()
        loader_class = loaders.get(extension)
        if loader_class:
            loader = loader_class(file_path)
            pages = loader.load_and_split()

            # Use a unique collection name for each file
            collection_name = os.path.basename(file_path)  # Name based on the file name
            retrievers[file_path] = Chroma.from_documents(
                pages, 
                embedding=embeddings, 
                collection_name=collection_name
            ).as_retriever()
            
        else:
            logging.warning(f"Unsupported file format: {file_path}")

    sorted_retrievers = {key: retrievers[key] for key in sorted(retrievers)}
    return sorted_retrievers

# ---- Initial Streamlit Configuration ----
st.set_page_config(
    page_title="DSMate",  
    menu_items={
        'About': "This is an application developed by Darío González Lema for the Distributed Systems course."
    }
)
st.sidebar.title("DSMate")
st.sidebar.caption("Virtual Assistant for the Distributed Systems course (EPI Gijón, Universidad de Oviedo)")

# ---- Set up the LLM and embeddings ----
llm = OllamaLLM(model="mistral:latest")
embeddings = OllamaEmbeddings(model="mistral")
parser = StrOutputParser()

prompt_template = """
    You are an intelligent AI assistant named DSMate. Your task is to carefully read the provided context from multiple documents and 
    then offer clear, accurate, and helpful answers to any questions based on that context. You will answer both theoretical and practical 
    questions about Distributed Systems, a subject in the Computer Science Engineering program, taught at 
    the Polytechnic School of Gijón, University of Oviedo. If you cannot find sufficient relevant information in the context to answer a 
    question, respond with: 'Sorry, I don't have enough information to answer that question.' Additionally, if the question is asked in 
    English, you must respond in English; if it is asked in Spanish, you must respond in Spanish. In case you are asked to do something 
    related to programming, you should prioritize the C language running on an Ubuntu 20.04 as this is the main language of the subject.
    There will also be some lab sessions with Java.
    "

    Context: {context}

    Question: {question}
"""

# ---- Load retrievers on server startup ----
try:
    retrievers = initialize_retrievers(directory="files/")
except ValueError as e:
    retrievers = {}
    logging.error(f"Error initializing retrievers: {e}")

# ---- Set up the authentication ----
with open('credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=True
)

def log_activity(user_data, msg):
    """
    Callback function to log the user's activity.
    """
    logging.info(f"User {user_data} has {msg}")

logging.basicConfig(
    filename='user_activity.log',  
    level=logging.INFO,  
    format='%(asctime)s - %(message)s',  
)

# ---- Main Application ----
if __name__ == "__main__":
    if not retrievers:
        st.error("No documents are available. Please add files to the 'files/' directory and restart the server.")
    else:
        # Chat History Initialization 
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = PromptTemplate.from_template(prompt_template)

        try:
            # Handle login with activity logging
            authenticator.login(callback=lambda user_data: log_activity(st.session_state["email"], "login"))
        except Exception as e:
            st.error(e)

        if st.session_state['authentication_status']:
            # Authenticated user
            st.sidebar.write(f'Welcome *{st.session_state["name"]}*')
            email = st.session_state["email"]
            # Show logout button
            authenticator.logout(location="sidebar", callback=lambda user_data: log_activity(email, "logout")) 

            # File selection combo box
            selected_file = st.sidebar.selectbox(
                "Select a file for your query:",
                list(retrievers.keys()),
                format_func=lambda x: Path(x).stem
            )
            
            # Set the retriever based on the selected file
            retriever = retrievers[selected_file]
  
            # User input for a question
            prompt_input = st.chat_input("Enter your question...")
            if prompt_input:
                log_activity(email, "made a question")
                st.session_state.messages.append({"role": "user", "content": prompt_input})
                with st.chat_message("user"):
                    st.markdown(prompt_input)

                # Generate the response
                with st.spinner("Generating response..."):
                    context = retriever.invoke(prompt_input)
                    response = llm.invoke(prompt.format(context=context, question=prompt_input))
                    with st.chat_message("assistant"):
                        st.markdown(response)

                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})

        elif st.session_state['authentication_status'] is False:
            # Authentication failed
            st.error('Username/password is incorrect')

        elif st.session_state['authentication_status'] is None:
            # Logged out or not authenticated
            st.warning('Please enter your username and password')
            st.session_state.messages = []  # Clear chat history on logout
