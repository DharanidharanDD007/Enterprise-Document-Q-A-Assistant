from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
# --- IMPORT THE NEW AUDIO FUNCTION CORRECTLY ---
from rag_engine import ingest_document, ask_question, generate_knowledge_graph_data, generate_audio_podcast

app = FastAPI()

# Allow the frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    print(f"📥 Receiving file: {file.filename}")
    
    # Save the uploaded file temporarily
    file_location = f"temp_{file.filename}"
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the file using our engine
        result = ingest_document(file_location)
        
    except Exception as e:
        print(f"❌ Server Error during upload: {e}")
        result = f"Server Error: {e}"
        
    finally:
        # Clean up (delete temp file) if it exists
        if os.path.exists(file_location):
            os.remove(file_location)
            print("🧹 Temp file cleaned up.")
    
    return {"message": result}

@app.get("/ask")
async def ask(query: str):
    answer = ask_question(query)
    return {"answer": answer}

@app.get("/generate-graph")
async def get_graph():
    print("🧠 Generating Knowledge Graph...")
    graph_data = generate_knowledge_graph_data()
    return graph_data

# --- UPDATED PODCAST ENDPOINT ---
@app.get("/generate-podcast")
async def get_podcast():
    print("🎙️ Generating Audio Podcast...")
    # Call the new function name
    data = generate_audio_podcast()
    return data