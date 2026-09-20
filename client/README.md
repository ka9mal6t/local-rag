# Client README

This folder contains the desktop application for Local RAG.

Related docs:
- [Main project README](../README.md)
- [API README](../api/README.md)
- [License](../LICENSE)

## Purpose

The client is a PySide6 desktop interface for interacting with the Local RAG backend. It provides:
- chat pages
- document management
- settings configuration
- multiple chat sessions
- document-based and general chat modes

## Main files

### `main.py`
Entry point for the desktop app.

It creates the Qt application, opens `MainWindow`, and runs the event loop.

### `config.py`
Stores the backend API URL.

Default value:

```python
API_URL = "http://127.0.0.1:5000"
```

### `services/api_client.py`
Client for communication with the Flask backend.

Supported operations:
- upload PDF
- list documents
- delete document
- send a general chat request
- send a document-grounded chat request

### `ui/main_window.py`
The main application shell.

Contains the left sidebar navigation and page switching between:
- Dashboard
- Documents
- General chat
- Document chat
- Settings

### `ui/chat_page.py`
The main chat interface.

It supports:
- chat history
- multiple conversation sessions
- streaming AI responses
- answer rendering in paragraphs and lists
- Sources block under assistant responses
- clean UI with no heavy wrappers

### `ui/documents_page.py`
Document management page.

It lets the user:
- upload PDF files
- view currently indexed documents
- delete documents from the local knowledge base

### `ui/settings_page.py`
Settings form for the API URL.

## Running the client

From the project root:

```bash
python -m client.main
```

Make sure the Flask backend is running before opening the client.

## Requirements

The client depends on:

```text
PySide6>=6.8
requests>=2.32
```

You can install them with:

```bash
pip install -r client\requirements.txt
```

## Typical user flow

1. Start the API.
2. Start the desktop client.
3. Upload one or more PDFs.
4. Open the Document chat mode.
5. Ask questions about the uploaded content.
6. Use the general chat mode for non-document conversations.

## Notes

The desktop application is designed as a local front-end for the backend. It does not store the PDF content itself; it relies on the backend and the FAISS index to retrieve relevant context.
