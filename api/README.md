# API README

This folder contains the Flask backend for the Local RAG application.

Related docs:
- [Main project README](../README.md)
- [Client README](../client/README.md)
- [License](../LICENSE)

## Purpose

The API provides the main application logic for:
- uploading and deleting PDFs
- indexing uploaded documents into a FAISS vector store
- retrieving relevant chunks from the local knowledge base
- answering questions with a local Ollama model
- storing conversation history in SQLite
- exposing routes used by the desktop client

## Main files

### `__init__.py`
Creates the Flask application instance and initializes the database and RAG service.

### `config.py`
Contains the LLM configuration:
- `ai_model` — selected Ollama model
- `ollama_host` — backend URL for Ollama
- `FAIL_PDF_SEARCH` — fallback text used when context does not contain an answer

### `route.py`
Registers the application blueprints:
- ask endpoints
- PDF-related endpoints
- general chat endpoints
- document upload endpoints

### `main.py`
Runs the Flask app in debug mode for local development.

## Routes

### `/ai/upload-pdf`
POST route to upload a PDF file.

Behavior:
- validates the uploaded file is a PDF
- stores the file in `api/static/pdf/`
- indexes the document via the RAG service
- returns updated document list

### `/ai/documents`
GET route to list uploaded documents.

### `/ai/documents/<filename>`
DELETE route to remove one uploaded document.

### `/ai/chat`
POST route for general chat without document grounding.

It:
- creates or reuses a chat session
- keeps recent conversation history
- summarizes older messages when needed
- streams model output back to the client

### `/ai/chat_pdf`
POST route for document-grounded chat.

It:
- runs retrieval from the FAISS index and keyword index
- reranks relevant chunks
- sends the context to the local model
- streams the answer and source information

## Database

The application uses SQLite with Flask-SQLAlchemy.

Model files:
- `api/models/chat.py`
- `api/models/message.py`

These tables store:
- chat sessions
- message history
- summary text for long conversations

## RAG services

### `api/services/rag_service.py`
Main orchestrator for retrieval and index management.

Responsibilities:
- building the FAISS index
- rebuilding after document add/delete
- updating the keyword corpus
- returning top relevant chunks for a query

### `api/services/rag.py`
Answer generation and stream generation.

It constructs the context from retrieved chunks and sends it to the LLM.
The sources are extracted from the metadata returned by retrieval.

### `api/services/vector_store.py`
Stores and retrieves embeddings and metadata from FAISS on disk.

### `api/services/keyword_service.py`
Runs BM25 keyword matching against the stored text corpus.

### `api/services/document_loader.py`
Reads PDF files and splits text into chunks.

### `api/services/embedding_service.py`
Creates embedding vectors and query embeddings.

### `api/services/rerank_service.py`
Reranks the combined document chunks and keeps the most relevant ones.

## Local execution

From the project root:

```bash
python -m flask --app api.main run --debug
```

The backend expects Ollama to be available and reachable at the configured host.

## Generated runtime data

The API creates runtime artifacts such as:
- uploaded PDFs in `api/static/pdf/`
- FAISS index files in `api/vector_index/`
- the SQLite database in the app runtime directory
- logs under `logs/`

These are generated while running the app.

## Notes

The backend is intentionally local-first and designed to work without external hosted AI APIs. The full retrieval and generation flow is local to the machine where the app is running.
