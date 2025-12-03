# 🚀 Enterprise RAG - Advanced Document Analysis System

A comprehensive Retrieval-Augmented Generation (RAG) application with advanced features including citations, confidence scoring, document summarization, and multi-document support.

## ✨ Key Features

### Core Features
- 📄 **PDF Document Processing** - Upload and process PDF documents
- 💬 **Intelligent Q&A** - Ask questions about uploaded documents
- 📚 **Citation & Source Tracking** - See exact document locations for answers
- 📊 **Confidence Scoring** - Know how confident the system is in each answer
- 📝 **Document Summarization** - Auto-generate comprehensive summaries
- 🕸️ **Knowledge Graph Visualization** - Interactive graph of document relationships
- 🎙️ **Audio Podcast Generation** - Convert documents to audio summaries
- 🎤 **Voice Input** - Speak your questions using Web Speech API
- 📦 **Multi-Document Support** - Query across multiple documents

### Advanced Features
- ✅ **Proper Error Handling** - Comprehensive error handling and validation
- 📋 **API Documentation** - Auto-generated OpenAPI/Swagger docs
- ⚙️ **Configuration Management** - Environment-based configuration
- 📝 **Structured Logging** - Professional logging system
- 🔒 **File Validation** - Type and size validation for uploads
- 🎯 **Source Highlighting** - See relevant passages from documents

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with LangChain and ChromaDB
- **Frontend**: React.js with modern dark-themed UI
- **LLM**: Ollama (Llama 3) - running locally for privacy
- **Vector Database**: ChromaDB for document embeddings
- **Text-to-Speech**: Google TTS (gTTS)

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Ollama installed and running (with llama3 model pulled)
- Internet connection (for Google TTS)

## 🚀 Quick Start

### 1. Install Ollama

```bash
# Install Ollama from https://ollama.ai
# Pull the llama3 model
ollama pull llama3
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file (optional - uses defaults if not present)
cp .env.example .env
# Edit .env with your preferences

# Run the backend server
python run_server.py
# or
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### 3. Frontend Setup

```bash
cd client
npm install
npm start
```

Frontend will run on `http://localhost:3000`

### 4. Access API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

## 📖 Usage

1. **Upload Document**: Click "Upload & Index" to process a PDF
2. **Ask Questions**: Type or speak questions about the document
3. **View Citations**: See source locations and relevant passages
4. **Check Confidence**: View confidence scores for each answer
5. **Generate Summary**: Click "Generate Summary" for document overview
6. **View Knowledge Graph**: Visualize document relationships
7. **Listen to Podcast**: Generate audio summary of document

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=False

# LLM Configuration
LLM_MODEL=llama3
LLM_TEMPERATURE=0
EMBEDDING_MODEL=llama3

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=5

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf
```

## 📡 API Endpoints

### Document Management
- `POST /upload-doc` - Upload and process PDF document
- `GET /documents` - List all uploaded documents
- `GET /documents/{name}` - Get document information

### Query & Analysis
- `GET /ask?query={question}` - Ask a question (with citations & confidence)
- `POST /ask` - Ask a question (JSON body)
- `GET /summarize` - Generate document summary
- `GET /generate-graph` - Generate knowledge graph
- `GET /generate-podcast` - Generate audio podcast

### Health & Info
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🎯 Response Format

### Ask Question Response
```json
{
  "answer": "The answer text...",
  "confidence": 0.85,
  "citations": [
    {
      "id": 1,
      "text": "Relevant passage...",
      "page": 5,
      "source": "document.pdf",
      "relevance_score": 0.92
    }
  ],
  "sources": ["document.pdf"],
  "source_count": 3,
  "audio": "base64_encoded_mp3..." // if voice_mode=true
}
```

### Summary Response
```json
{
  "status": "success",
  "summary": "Comprehensive summary text...",
  "document_name": "document.pdf",
  "chunk_count": 45,
  "page_count": 12,
  "generated_at": 1234567890
}
```

## 🛠️ Development

### Project Structure
```
Enterprise_RAG/
├── main.py              # FastAPI backend server
├── rag_engine.py        # Core RAG logic
├── config.py            # Configuration management
├── logger_config.py     # Logging setup
├── requirements.txt     # Python dependencies
├── client/              # React frontend
│   ├── src/
│   │   ├── App.js       # Main React component
│   │   ├── GraphModal.js
│   │   ├── PodcastModal.js
│   │   └── SummaryModal.js
│   └── package.json
└── db_storage_*/        # ChromaDB storage
```

### Key Improvements Made

1. ✅ Fixed duplicate endpoints
2. ✅ Added missing dependencies (gTTS)
3. ✅ Implemented citation tracking
4. ✅ Added confidence scoring
5. ✅ Created document summarization
6. ✅ Multi-document support
7. ✅ Configuration management (.env)
8. ✅ Proper logging system
9. ✅ File validation
10. ✅ Enhanced error handling
11. ✅ API documentation
12. ✅ Frontend enhancements

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Make sure Ollama is running
ollama serve

# Verify model is available
ollama list
```

### Port Already in Use
```bash
# Change port in .env file
PORT=8001
```

### Frontend Can't Connect to Backend
- Check CORS_ORIGINS in .env
- Verify backend is running on correct port
- Check browser console for errors

## 📊 Performance Tips

- Use smaller chunk sizes for faster processing
- Reduce RETRIEVAL_K for faster queries
- Enable file logging only in development
- Use SSD storage for better ChromaDB performance

## 🔒 Security Notes

- Currently configured for local development
- Add authentication for production use
- Configure CORS properly for production
- Validate all user inputs
- Implement rate limiting

## 🚀 Future Enhancements

See `FEATURE_ENHANCEMENTS.md` for a comprehensive list of potential features including:
- Multi-modal document analysis
- Advanced semantic search
- User authentication
- Document versioning
- Integration with external systems

## 📝 License

This project is open source and available for educational and portfolio purposes.

## 👨‍💻 Author

Enterprise RAG System - Advanced Document Analysis Platform

## 🙏 Acknowledgments

- LangChain for RAG framework
- ChromaDB for vector storage
- Ollama for local LLM
- FastAPI for backend framework
- React for frontend framework

---

**Built with ❤️ for Enterprise Document Analysis**


