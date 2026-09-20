# Local RAG

## Documentation

- [Project overview](#local-rag)
- [API docs](api/README.md)
- [Client docs](client/README.md)
- [License](LICENSE)

Local RAG is a desktop application for working with local PDF documents using Retrieval-Augmented Generation (RAG). The project combines a Flask API, a local Ollama-powered LLM, a FAISS vector index, and a PySide6 desktop client.

The app allows you to:
- upload and index PDF documents
- ask questions only from the indexed document set
- run a regular chat without uploaded files
- keep multiple chat sessions
- delete uploaded documents and chats
- see source names in answers from the indexed files

## Project overview

The project has three main parts:

1. API layer
   - Flask application in `api/`
   - exposes document upload, document list, document deletion, and chat endpoints
   - loads and manages the RAG service

2. RAG pipeline
   - reads PDF text
   - splits text into chunks
   - embeds chunks using an embedding model
   - stores vectors in FAISS
   - combines vector and keyword search
   - reranks results
   - sends the relevant context to the local LLM

3. Desktop client
   - PySide6 application in `client/`
   - visual chat interface
   - Documents page for upload/delete management
   - settings page for API URL configuration
   - session history and multiple chat support

## Features

- PDF upload and indexing
- document listing and deletion
- local chat without documents
- document-grounded chat
- multiple chat windows/sessions
- persistent local chat history
- answer sources displayed in the UI
- local AI inference via Ollama
- desktop interface created with PySide6

## Architecture

The application roughly follows this flow:

PDF file -> PDF parser -> chunking -> embeddings -> FAISS index -> retrieval -> reranking -> Ollama model -> answer + sources

Main components:

- `api/main.py` — application bootstrap
- `api/config.py` — model name and server configuration
- `api/route.py` — route registration
- `api/routes/upload_pdf.py` — PDF upload/list/delete endpoints
- `api/routes/chat.py` — general chat endpoint
- `api/routes/chat_pdf.py` — document-grounded chat endpoint
- `api/services/rag_service.py` — index management and retrieval pipeline
- `api/services/rag.py` — answer generation and source extraction
- `api/services/vector_store.py` — FAISS persistence layer
- `api/services/keyword_service.py` — BM25 keyword search
- `api/services/document_loader.py` — PDF text extraction and chunking
- `api/services/ai_service.py` — general LLM calls and summary logic
- `client/ui/chat_page.py` — chat UI and message rendering
- `client/ui/documents_page.py` — document management UI
- `client/ui/main_window.py` — navigation and app shell
- `client/ui/settings_page.py` — settings form

## Requirements

Before running the project, make sure you have:

- Python 3.10+
- Ollama installed and running locally
- a model pulled in Ollama, for example `llama3.2:latest`
- access to the local API at `http://127.0.0.1:11434`

Recommended Python dependencies are listed in:
- `requirements.txt` at the project root
- `client/requirements.txt`

## Environment and configuration

The backend configuration is in `api/config.py`.

Important settings:

- `ai_model` — model name used by Ollama
- `ollama_host` — Ollama host address, default: `http://127.0.0.1:11434`
- `FAIL_PDF_SEARCH` — fallback text returned when the answer is not found in uploaded documents

## Installation

1. Clone the repository
2. Create a virtual environment
3. Install requirements

Example:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r client\requirements.txt
```

On Linux/macOS activate with:

```bash
source .venv/bin/activate
```

## Run Ollama

Start Ollama and ensure the model is available.

Example:

```bash
ollama pull llama3.2:latest
ollama serve
```

## Run the API

From the project root:

```bash
python -m flask --app api.main run --debug
```

The API is available through the Flask app and uses the `ai` blueprint with routes like:

- `/ai/chat`
- `/ai/chat_pdf`
- `/ai/upload-pdf`
- `/ai/documents`

## Run the desktop client

From the project root:

```bash
python -m client.main
```

The desktop app starts the PySide6 interface and connects to the Flask backend by default at:

```text
http://127.0.0.1:5000
```

You can adjust this value in the client settings page or in `client/config.py`.

## Data and generated files

The project creates runtime files such as:

- `api/static/pdf/` uploaded PDFs
- `api/vector_index/` FAISS index files
- `data/chat_history.json` app chat history
- SQLite database files under the app runtime folders

These files are generated on use and are not part of the source code itself.

## Usage examples

### General chat

Use this mode when no PDF files are uploaded or when you want a general conversation without document grounding.

### Document-based chat

Upload one or more PDFs, then ask a question. The app retrieves the relevant text chunks, reranks them, and sends the context to Ollama.

### Document management

On the Documents page you can:
- upload a new PDF
- list all indexed PDFs
- delete a document from the local knowledge base

## Development notes

Important implementation details:

- FAISS is used for dense vector search
- BM25 is used for keyword scoring
- results are combined before reranking
- answers and sources are returned in structured form
- chat sessions are stored locally so the desktop app can restore history

## License

This project is open-source and distributed under the MIT License.
See the full text in [LICENSE](LICENSE).

## Contributing

Contributions are welcome.

You can:
- open issues
- suggest improvements
- submit pull requests
- improve the prompt strategy or UX

## Notes

This app is designed as a local-first assistant for personal or internal knowledge work. It does not require a remote API and depends on local infrastructure such as Ollama and a machine with enough RAM and CPU to run embeddings and the LLM model.
