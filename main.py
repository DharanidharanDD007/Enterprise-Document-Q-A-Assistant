"""
FastAPI Backend for Enterprise RAG Application
Enhanced with proper error handling, validation, and new features
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
import os
from pathlib import Path
from typing import Optional, Tuple

from rag_engine import (
    ingest_document, 
    ask_question, 
    generate_knowledge_graph_data, 
    generate_audio_podcast,
    generate_document_summary,
    list_documents,
    get_document_info
)
from config import config
from logger_config import logger

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise RAG API",
    description="Retrieval-Augmented Generation API for Enterprise Document Analysis",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    voice_mode: bool = False
    document_name: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Ensure upload directory exists
UPLOAD_DIR = Path(config.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)


def validate_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in config.ALLOWED_EXTENSIONS:
        return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
    
    # Check file size (if available)
    if hasattr(file, 'size'):
        max_size = config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        if file.size > max_size:
            return False, f"File size exceeds maximum of {config.MAX_FILE_SIZE_MB}MB"
    
    return True, None


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Enterprise RAG API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Document Upload & Processing",
            "Question Answering with Citations",
            "Confidence Scoring",
            "Document Summarization",
            "Knowledge Graph Generation",
            "Audio Podcast Generation",
            "Multi-Document Support"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Enterprise RAG API"}


@app.post("/upload-doc", tags=["Documents"])
async def upload_doc(file: UploadFile = File(...), document_name: Optional[str] = None):
    """
    Upload and process a PDF document
    
    - **file**: PDF file to upload
    - **document_name**: Optional name for the document
    """
    logger.info(f"Received upload request: {file.filename}")
    
    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        logger.warning(f"File validation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    file_location = None
    try:
        # Save uploaded file temporarily
        file_location = UPLOAD_DIR / f"temp_{file.filename}"
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to: {file_location}")
        
        # Process the file
        result = ingest_document(str(file_location), document_name)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temporary file
        if file_location and file_location.exists():
            try:
                file_location.unlink()
                logger.debug("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")


@app.get("/ask", tags=["Query"])
async def ask(
    query: str = Query(..., description="Question to ask"),
    voice_mode: bool = Query(False, description="Generate audio response"),
    document_name: Optional[str] = Query(None, description="Specific document to query")
):
    """
    Ask a question about uploaded documents
    
    Returns answer with citations, confidence score, and sources
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    logger.info(f"Processing query: {query[:50]}...")
    
    try:
        result = ask_question(query, return_audio=voice_mode, document_name=document_name)
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/ask", tags=["Query"])
async def ask_post(request: QueryRequest):
    """
    Ask a question (POST method with JSON body)
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    logger.info(f"Processing query (POST): {request.query[:50]}...")
    
    try:
        result = ask_question(
            request.query, 
            return_audio=request.voice_mode, 
            document_name=request.document_name
        )
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/documents", tags=["Documents"])
async def get_documents():
    """List all uploaded documents"""
    try:
        documents = list_documents()
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.get("/documents/{document_name}", tags=["Documents"])
async def get_document(document_name: str):
    """Get information about a specific document"""
    try:
        doc_info = get_document_info(document_name)
        if not doc_info:
            raise HTTPException(status_code=404, detail=f"Document '{document_name}' not found")
        return doc_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting document info: {str(e)}")


@app.get("/summarize", tags=["Analysis"])
async def summarize(document_name: Optional[str] = Query(None, description="Specific document to summarize")):
    """Generate a comprehensive summary of the document"""
    logger.info("Generating document summary...")
    
    try:
        result = generate_document_summary(document_name)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@app.get("/generate-graph", tags=["Analysis"])
async def get_graph(document_name: Optional[str] = Query(None, description="Specific document for graph")):
    """Generate knowledge graph from document"""
    logger.info("Generating knowledge graph...")
    
    try:
        graph_data = generate_knowledge_graph_data(document_name)
        return graph_data
    except Exception as e:
        logger.error(f"Error generating graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")


@app.get("/generate-podcast", tags=["Analysis"])
async def get_podcast(document_name: Optional[str] = Query(None, description="Specific document for podcast")):
    """Generate audio podcast from document"""
    logger.info("Generating audio podcast...")
    
    try:
        data = generate_audio_podcast(document_name)
        if not data:
            raise HTTPException(status_code=404, detail="No document content available for podcast generation")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating podcast: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
