import json
from pathlib import Path
from urllib.parse import quote
import requests

from client.config import API_URL


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def upload_pdf(self, path: str) -> dict:
        file_path = Path(path)
        with file_path.open("rb") as file:
            response = requests.post(
                self._url("/ai/upload-pdf"),
                files={"file": (file_path.name, file, "application/pdf")},
                timeout=120,
            )

        if not response.ok:
            raise ApiError(self._error(response))

        return response.json()

    def list_documents(self) -> dict:
        response = requests.get(
            self._url("/ai/documents"),
            timeout=60,
        )

        if not response.ok:
            raise ApiError(self._error(response))

        return response.json()

    def delete_document(self, filename: str) -> dict:
        encoded_name = quote(filename, safe="")
        response = requests.delete(
            self._url(f"/ai/documents/{encoded_name}"),
            timeout=60,
        )

        if not response.ok:
            raise ApiError(self._error(response))

        return response.json()

    def ask_pdf(self, question: str) -> dict:
        response = requests.post(
            self._url("/ai/ask_pdf"),
            json={"question": question},
            timeout=180,
        )

        if not response.ok:
            raise ApiError(self._error(response))

        return response.json()

    def stream_pdf_chat(self, question: str):
        response = requests.post(
            self._url("/ai/chat_pdf"),
            json={"question": question},
            stream=True,
            timeout=(10, 300),
        )

        if not response.ok:
            raise ApiError(self._error(response))

        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.rstrip("\r")
            if not line.startswith("data:"):
                continue

            data = line[5:]
            yield data[1:] if data.startswith(" ") else data

    def stream_chat(self, question: str, chat_id: int | None = None):
        payload = {"question": question}
        if chat_id is not None:
            payload["chat_id"] = chat_id

        response = requests.post(
            self._url("/ai/chat"),
            json=payload,
            stream=True,
            timeout=(10, 300),
        )

        if not response.ok:
            raise ApiError(self._error(response))

        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue

            line = raw_line.rstrip("\r")
            if not line.startswith("data:"):
                continue

            data = line[5:]
            yield data[1:] if data.startswith(" ") else data

    @staticmethod
    def _error(response) -> str:
        try:
            data = response.json()
            return data.get("error", response.text)
        except Exception:
            return response.text or f"HTTP {response.status_code}"
