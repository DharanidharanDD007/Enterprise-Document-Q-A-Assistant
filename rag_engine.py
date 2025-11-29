import os
import shutil
import json
import re
import ast
import base64
import time # <--- Added time for unique folders
from io import BytesIO
from gtts import gTTS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# GLOBAL VARIABLE to track the current database folder
CURRENT_DB_DIR = "db_storage_latest"

# --- 1. INGESTION FUNCTION (Creates Fresh DB Every Time) ---
def ingest_document(file_path):
    global CURRENT_DB_DIR
    
    # Generate a unique folder name to avoid Windows file locks (e.g. db_storage_1732049...)
    timestamp = int(time.time())
    NEW_DB_DIR = f"db_storage_{timestamp}"

    print(f"🧹 Creating fresh database at: {NEW_DB_DIR}")

    # Load and Split
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Embed and Store
    embedding_function = OllamaEmbeddings(model="llama3")
    
    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=embedding_function,
        persist_directory=NEW_DB_DIR
    )
    
    # Update the global pointer so other functions know where to look
    # Try to cleanup the old one (it might fail on Windows, but that's okay now)
    if os.path.exists(CURRENT_DB_DIR) and CURRENT_DB_DIR != NEW_DB_DIR:
        try:
            shutil.rmtree(CURRENT_DB_DIR, ignore_errors=True)
        except:
            pass
            
    CURRENT_DB_DIR = NEW_DB_DIR
    
    return "Document Processed! Old data wiped."

# --- 2. CHAT FUNCTION ---
def ask_question(query):
    global CURRENT_DB_DIR
    embedding_function = OllamaEmbeddings(model="llama3")
    
    # Point to the CURRENT folder
    vector_db = Chroma(persist_directory=CURRENT_DB_DIR, embedding_function=embedding_function)
    
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    llm = ChatOllama(model="llama3", temperature=0)

    prompt_template = """
    You are an intelligent Enterprise Assistant. 
    Use the following pieces of context to answer the question at the end.
    Rules:
    1. Answer strictly based on the context provided.
    2. If the answer is not in the context, say "I cannot find the answer in this document."
    
    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    response = qa_chain.invoke({"query": query})
    return response['result']

# --- 3. GRAPH FUNCTION ---
def generate_knowledge_graph_data():
    global CURRENT_DB_DIR
    embedding_function = OllamaEmbeddings(model="llama3")
    
    context_text = ""
    if os.path.exists(CURRENT_DB_DIR):
        try:
            vector_db = Chroma(persist_directory=CURRENT_DB_DIR, embedding_function=embedding_function)
            collection_data = vector_db.get() 
            docs = collection_data['documents']
            if docs:
                context_text = "\n\n".join(docs[:4])
        except Exception as e:
            print(f"⚠️ DB Access Warning: {e}")

    if not context_text:
        context_text = "Analysis pending."

    prompt = f"""
    Extract a Knowledge Graph from the text below.
    Return ONLY a JSON object. No intro.
    Format:
    {{
      "nodes": [{{"id": "ConceptName", "group": 1}}],
      "links": [{{"source": "ConceptName", "target": "OtherConcept", "relation": "relationship"}}]
    }}
    Text:
    {context_text}
    """

    print("🧠 Asking Llama 3 for graph JSON...")
    llm = ChatOllama(model="llama3", temperature=0) 
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        clean_content = re.sub(r"```json", "", content)
        clean_content = re.sub(r"```", "", clean_content)
        
        json_match = re.search(r"\{.*\}", clean_content, re.DOTALL)
        if json_match:
            clean_content = json_match.group(0)

        try:
            graph_data = json.loads(clean_content)
        except:
            graph_data = ast.literal_eval(clean_content)

        if "nodes" in graph_data and "links" in graph_data:
            return graph_data

    except Exception:
        pass

    return {
        "nodes": [{"id": "No Data", "group": 1}],
        "links": []
    }

# --- 4. PODCAST FUNCTION ---
def generate_audio_podcast():
    global CURRENT_DB_DIR
    embedding_function = OllamaEmbeddings(model="llama3")
    
    context_text = ""
    if os.path.exists(CURRENT_DB_DIR):
        try:
            vector_db = Chroma(persist_directory=CURRENT_DB_DIR, embedding_function=embedding_function)
            collection_data = vector_db.get() 
            docs = collection_data['documents']
            if docs:
                context_text = "\n\n".join(docs[:4])
        except Exception:
            pass

    if not context_text:
        return None

    prompt = f"""
    Write a lively, engaging 1-minute podcast intro summarizing this document.
    Start with "Welcome back! Today we're analyzing a new file..."
    Text to summarize:
    {context_text}
    """

    print("🎙️ Generating Script...")
    llm = ChatOllama(model="llama3", temperature=0.7)
    
    try:
        response = llm.invoke(prompt)
        script_text = response.content.strip()
        
        print("🔊 Converting to MP3...")
        mp3_fp = BytesIO()
        tts = gTTS(text=script_text, lang='en')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        audio_b64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        return {"audio": audio_b64, "text": script_text}

    except Exception as e:
        print(f"❌ Podcast Error: {e}")
        return None