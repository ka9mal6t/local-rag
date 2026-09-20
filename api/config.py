import os

ai_model = "llama3.2:latest"
ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

FAIL_PDF_SEARCH = "I cannot find the answer in the document."
