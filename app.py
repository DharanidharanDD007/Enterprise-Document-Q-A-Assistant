import streamlit as st
import os
import tempfile

# --- CONFIGURATION ---
st.set_page_config(page_title="Local Enterprise Q&A", page_icon="🦙", layout="centered")
st.title("🦙 Enterprise Q&A (Local Ollama)")

# --- IMPORTS ---
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.chains import RetrievalQA
    from langchain_community.chat_models import ChatOllama
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    st.error(f"❌ Library Missing: {e}")
    st.info("Run this command: pip install langchain langchain-community langchain-text-splitters faiss-cpu pypdf")
    st.stop()

# --- SESSION STATE ---
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR: DOCUMENT UPLOAD ---
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    process_button = st.button("Process Document", type="primary")
    
    st.markdown("---")
    st.caption("Using Model: **llama3**")

    # Reset Button
    if st.button("Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# --- LOGIC: PROCESS PDF ---
if uploaded_file and process_button:
    with st.spinner("Processing PDF with Ollama..."):
        try:
            # 1. Save temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            # 2. Load PDF
            loader = PyPDFLoader(tmp_path)
            documents = loader.load()
            
            # 3. Split Text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(documents)

            # 4. Create Embeddings (Using Ollama)
            # Make sure 'llama3' is pulled in your terminal
            embeddings = OllamaEmbeddings(model="llama3") 
            
            # 5. Store in Vector Database (FAISS)
            st.session_state.vector_store = FAISS.from_documents(splits, embeddings)

            st.success(f"✅ Indexed {len(splits)} chunks!")
            os.remove(tmp_path)
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("👉 Make sure Ollama is running! Run `ollama serve` in a terminal.")

# --- CHAT INTERFACE ---
# Display History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if user_question := st.chat_input("Ask a question about the PDF..."):
    
    if st.session_state.vector_store is None:
        st.warning("⚠️ Please upload and process a PDF first.")
    else:
        # 1. Show User Message
        with st.chat_message("user"):
            st.markdown(user_question)
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        # 2. Generate Answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Connect to Local Ollama
                    llm = ChatOllama(model="llama3", temperature=0)
                    
                    # Create Chain
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=st.session_state.vector_store.as_retriever(search_kwargs={"k": 3})
                    )
                    
                    # Get Response
                    response = qa_chain.invoke({"query": user_question})
                    answer_text = response['result']
                    
                    st.markdown(answer_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer_text})
                    
                except Exception as e:
                    st.error(f"Error: {e}")