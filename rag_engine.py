"""
Enhanced RAG Engine with Citations, Confidence Scoring, Summarization, and Multi-Document Support
"""
import os
import shutil
import json
import re
import ast
import base64
import time
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from gtts import gTTS

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from config import config
from logger_config import logger

# Global variables
CURRENT_DB_DIR = "db_storage_latest"
DOCUMENT_METADATA: Dict[str, Dict] = {}  # Store document metadata
DOCUMENT_COLLECTIONS: Dict[str, str] = {}  # Map document names to DB directories


def text_to_audio_base64(text: str) -> Optional[str]:
    """Convert text to base64-encoded MP3 audio"""
    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang=config.TTS_LANGUAGE)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return base64.b64encode(mp3_fp.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Audio generation error: {e}")
        return None


def calculate_confidence_score(similarity_scores: List[float], source_count: int) -> float:
    """
    Calculate confidence score based on similarity scores and source count
    
    Args:
        similarity_scores: List of similarity scores from retrieval
        source_count: Number of source documents
        
    Returns:
        Confidence score between 0 and 1
    """
    if not similarity_scores:
        return 0.0
    
    # Average similarity score (normalized to 0-1)
    avg_similarity = sum(similarity_scores) / len(similarity_scores)
    
    # Source count factor (more sources = higher confidence, up to a point)
    source_factor = min(source_count / config.RETRIEVAL_K, 1.0)
    
    # Combined confidence score
    confidence = (avg_similarity * 0.7) + (source_factor * 0.3)
    
    return min(max(confidence, 0.0), 1.0)


def extract_citations(source_documents: List[Document], query: str) -> List[Dict]:
    """
    Extract citation information from source documents
    
    Args:
        source_documents: List of source documents from retrieval
        query: Original query
        
    Returns:
        List of citation dictionaries with metadata
    """
    citations = []
    
    for idx, doc in enumerate(source_documents, 1):
        citation = {
            "id": idx,
            "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "page": doc.metadata.get("page", "Unknown"),
            "source": doc.metadata.get("source", "Unknown"),
            "relevance_score": doc.metadata.get("score", 0.0)
        }
        citations.append(citation)
    
    return citations


def ingest_document(file_path: str, document_name: Optional[str] = None) -> Dict:
    """
    Ingest a document and create vector database
    
    Args:
        file_path: Path to the PDF file
        document_name: Optional name for the document
        
    Returns:
        Dictionary with ingestion results
    """
    global CURRENT_DB_DIR, DOCUMENT_METADATA
    
    try:
        # Generate unique folder name
        timestamp = int(time.time())
        NEW_DB_DIR = f"{config.DB_STORAGE_PREFIX}_{timestamp}"
        
        logger.info(f"Processing document: {file_path}")
        logger.info(f"Creating database at: {NEW_DB_DIR}")
        
        # Load and split document
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError("No content extracted from document")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        docs = text_splitter.split_documents(documents)
        
        logger.info(f"Split document into {len(docs)} chunks")
        
        # Create embeddings and store
        embedding_function = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        
        vector_db = Chroma.from_documents(
            documents=docs,
            embedding=embedding_function,
            persist_directory=NEW_DB_DIR
        )
        
        # Store metadata
        doc_name = document_name or os.path.basename(file_path)
        DOCUMENT_METADATA[doc_name] = {
            "name": doc_name,
            "path": file_path,
            "db_dir": NEW_DB_DIR,
            "chunk_count": len(docs),
            "page_count": len(documents),
            "upload_time": timestamp
        }
        
        # Update current DB directory
        if os.path.exists(CURRENT_DB_DIR) and CURRENT_DB_DIR != NEW_DB_DIR:
            try:
                shutil.rmtree(CURRENT_DB_DIR, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Could not remove old DB directory: {e}")
        
        CURRENT_DB_DIR = NEW_DB_DIR
        DOCUMENT_COLLECTIONS[doc_name] = NEW_DB_DIR
        
        logger.info(f"Document processed successfully: {doc_name}")
        
        return {
            "status": "success",
            "message": f"Document '{doc_name}' processed successfully",
            "document_name": doc_name,
            "chunks": len(docs),
            "pages": len(documents),
            "db_directory": NEW_DB_DIR
        }
        
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        return {
            "status": "error",
            "message": f"Error processing document: {str(e)}"
        }


def ask_question(query: str, return_audio: bool = False, document_name: Optional[str] = None) -> Dict:
    """
    Ask a question and get answer with citations and confidence score
    
    Args:
        query: User's question
        return_audio: Whether to generate audio response
        document_name: Optional specific document to query
        
    Returns:
        Dictionary with answer, citations, confidence, and optional audio
    """
    global CURRENT_DB_DIR
    
    try:
        # Determine which database to use
        db_dir = CURRENT_DB_DIR
        if document_name and document_name in DOCUMENT_COLLECTIONS:
            db_dir = DOCUMENT_COLLECTIONS[document_name]
        
        if not os.path.exists(db_dir):
            return {
                "answer": "No documents have been uploaded yet. Please upload a document first.",
                "confidence": 0.0,
                "citations": [],
                "sources": []
            }
        
        logger.info(f"Processing query: {query[:50]}...")
        
        # Load vector database
        embedding_function = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        vector_db = Chroma(persist_directory=db_dir, embedding_function=embedding_function)
        
        # Create retriever
        retriever = vector_db.as_retriever(search_kwargs={"k": config.RETRIEVAL_K})
        
        # Retrieve relevant documents
        retrieved_docs = retriever.get_relevant_documents(query)
        
        if not retrieved_docs:
            return {
                "answer": "I couldn't find relevant information to answer your question in the uploaded documents.",
                "confidence": 0.0,
                "citations": [],
                "sources": []
            }
        
        # Extract similarity scores (if available)
        similarity_scores = [doc.metadata.get("score", 0.8) for doc in retrieved_docs]
        
        # Create LLM chain
        llm = ChatOllama(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)
        
        prompt_template = """
        You are an intelligent Enterprise Assistant. 
        Answer the question based strictly on the context provided.
        
        Rules:
        1. Answer strictly based on the context provided.
        2. If the answer is not in the context, say "I cannot find the answer in this document."
        3. Be concise and accurate.
        4. Cite specific information when possible.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        # Get answer
        response = qa_chain.invoke({"query": query})
        answer_text = response['result']
        source_documents = response.get('source_documents', retrieved_docs)
        
        # Calculate confidence score
        confidence = calculate_confidence_score(similarity_scores, len(source_documents))
        
        # Extract citations
        citations = extract_citations(source_documents, query)
        
        # Get unique sources
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in source_documents]))
        
        # Build result
        result = {
            "answer": answer_text,
            "confidence": round(confidence, 2),
            "citations": citations,
            "sources": sources,
            "source_count": len(source_documents)
        }
        
        # Add audio if requested
        if return_audio:
            audio_b64 = text_to_audio_base64(answer_text)
            if audio_b64:
                result["audio"] = audio_b64
        
        logger.info(f"Query answered with confidence: {confidence:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        return {
            "answer": f"I encountered an error while processing your question: {str(e)}",
            "confidence": 0.0,
            "citations": [],
            "sources": []
        }


def generate_document_summary(document_name: Optional[str] = None) -> Dict:
    """
    Generate a comprehensive summary of the document
    
    Args:
        document_name: Optional specific document to summarize
        
    Returns:
        Dictionary with summary information
    """
    global CURRENT_DB_DIR
    
    try:
        # Determine which database to use
        db_dir = CURRENT_DB_DIR
        if document_name and document_name in DOCUMENT_COLLECTIONS:
            db_dir = DOCUMENT_COLLECTIONS[document_name]
        
        if not os.path.exists(db_dir):
            return {
                "status": "error",
                "message": "No documents available for summarization"
            }
        
        logger.info("Generating document summary...")
        
        # Load vector database
        embedding_function = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        vector_db = Chroma(persist_directory=db_dir, embedding_function=embedding_function)
        
        # Get all documents
        collection_data = vector_db.get()
        docs = collection_data.get('documents', [])
        
        if not docs:
            return {
                "status": "error",
                "message": "No content found in document"
            }
        
        # Use first 10 chunks for summary (or all if less)
        context_text = "\n\n".join(docs[:10])
        
        # Generate summary using LLM
        llm = ChatOllama(model=config.LLM_MODEL, temperature=0.3)
        
        summary_prompt = f"""
        Analyze the following document content and provide a comprehensive summary.
        
        Include:
        1. Main topics and themes
        2. Key points and findings
        3. Important dates, numbers, or metrics
        4. Conclusions or recommendations
        
        Format your response as:
        - Executive Summary (2-3 sentences)
        - Key Points (bullet list)
        - Important Details (paragraph)
        
        Document Content:
        {context_text}
        
        Summary:
        """
        
        response = llm.invoke(summary_prompt)
        summary_text = response.content.strip()
        
        # Extract key metrics
        metadata = DOCUMENT_METADATA.get(document_name or "current", {})
        
        result = {
            "status": "success",
            "summary": summary_text,
            "document_name": document_name or "Current Document",
            "chunk_count": len(docs),
            "page_count": metadata.get("page_count", "Unknown"),
            "generated_at": time.time()
        }
        
        logger.info("Summary generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return {
            "status": "error",
            "message": f"Error generating summary: {str(e)}"
        }


def generate_knowledge_graph_data(document_name: Optional[str] = None) -> Dict:
    """
    Generate knowledge graph data from document
    
    Args:
        document_name: Optional specific document
        
    Returns:
        Dictionary with graph nodes and links
    """
    global CURRENT_DB_DIR
    
    try:
        # Determine which database to use
        db_dir = CURRENT_DB_DIR
        if document_name and document_name in DOCUMENT_COLLECTIONS:
            db_dir = DOCUMENT_COLLECTIONS[document_name]
        
        if not os.path.exists(db_dir):
            return {
                "nodes": [{"id": "No Data", "group": 1}],
                "links": []
            }
        
        logger.info("Generating knowledge graph...")
        
        embedding_function = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        vector_db = Chroma(persist_directory=db_dir, embedding_function=embedding_function)
        
        collection_data = vector_db.get()
        docs = collection_data.get('documents', [])
        
        if not docs:
            return {
                "nodes": [{"id": "No Data", "group": 1}],
                "links": []
            }
        
        context_text = "\n\n".join(docs[:6])  # Use more chunks for better graph
        
        prompt = f"""
        Extract a Knowledge Graph from the text below.
        Return ONLY a JSON object. No intro text.
        
        Format:
        {{
          "nodes": [{{"id": "ConceptName", "group": 1, "label": "Display Name"}}],
          "links": [{{"source": "ConceptName", "target": "OtherConcept", "relation": "relationship type", "value": 1}}]
        }}
        
        Extract key concepts, entities, and their relationships.
        Create 5-15 nodes and 5-20 links.
        
        Text:
        {context_text}
        """
        
        llm = ChatOllama(model=config.LLM_MODEL, temperature=0)
        
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Clean JSON
        clean_content = re.sub(r"```json", "", content)
        clean_content = re.sub(r"```", "", clean_content)
        
        json_match = re.search(r"\{.*\}", clean_content, re.DOTALL)
        if json_match:
            clean_content = json_match.group(0)
        
        try:
            graph_data = json.loads(clean_content)
        except json.JSONDecodeError:
            try:
                graph_data = ast.literal_eval(clean_content)
            except:
                logger.warning("Could not parse graph JSON, returning default")
                graph_data = {
                    "nodes": [{"id": "Parse Error", "group": 1}],
                    "links": []
                }
        
        # Validate structure
        if "nodes" not in graph_data:
            graph_data["nodes"] = []
        if "links" not in graph_data:
            graph_data["links"] = []
        
        logger.info(f"Generated graph with {len(graph_data.get('nodes', []))} nodes")
        return graph_data
        
    except Exception as e:
        logger.error(f"Error generating knowledge graph: {e}")
        return {
            "nodes": [{"id": "Error", "group": 1}],
            "links": []
        }


def generate_audio_podcast(document_name: Optional[str] = None) -> Optional[Dict]:
    """
    Generate audio podcast from document
    
    Args:
        document_name: Optional specific document
        
    Returns:
        Dictionary with audio and script, or None on error
    """
    global CURRENT_DB_DIR
    
    try:
        # Determine which database to use
        db_dir = CURRENT_DB_DIR
        if document_name and document_name in DOCUMENT_COLLECTIONS:
            db_dir = DOCUMENT_COLLECTIONS[document_name]
        
        if not os.path.exists(db_dir):
            return None
        
        logger.info("Generating audio podcast...")
        
        embedding_function = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
        vector_db = Chroma(persist_directory=db_dir, embedding_function=embedding_function)
        
        collection_data = vector_db.get()
        docs = collection_data.get('documents', [])
        
        if not docs:
            return None
        
        context_text = "\n\n".join(docs[:4])
        
        prompt = f"""
        Write a lively, engaging 1-minute podcast intro summarizing this document.
        Start with "Welcome back! Today we're analyzing a new document..."
        Keep it conversational and engaging.
        Maximum 150 words.
        
        Text to summarize:
        {context_text}
        """
        
        llm = ChatOllama(model=config.LLM_MODEL, temperature=0.7)
        
        response = llm.invoke(prompt)
        script_text = response.content.strip()
        
        logger.info("Converting script to audio...")
        audio_b64 = text_to_audio_base64(script_text)
        
        if not audio_b64:
            return None
        
        return {
            "audio": audio_b64,
            "text": script_text
        }
        
    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
        return None


def list_documents() -> List[Dict]:
    """
    List all uploaded documents
    
    Returns:
        List of document metadata dictionaries
    """
    return list(DOCUMENT_METADATA.values())


def get_document_info(document_name: str) -> Optional[Dict]:
    """
    Get information about a specific document
    
    Args:
        document_name: Name of the document
        
    Returns:
        Document metadata or None if not found
    """
    return DOCUMENT_METADATA.get(document_name)
