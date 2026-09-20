from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QFrame, QListWidgetItem, QMessageBox
)


class UploadWorker(QObject):
    finished = Signal(str, list)
    error = Signal(str)

    def __init__(self, client, path):
        super().__init__()
        self.client = client
        self.path = path

    def run(self):
        try:
            result = self.client.upload_pdf(self.path)
            self.finished.emit(result.get("message", "PDF uploaded successfully"), result.get("documents", []))
        except Exception as exc:
            self.error.emit(str(exc))


class DeleteWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, client, filename):
        super().__init__()
        self.client = client
        self.filename = filename

    def run(self):
        try:
            result = self.client.delete_document(self.filename)
            self.finished.emit(result.get("documents", []))
        except Exception as exc:
            self.error.emit(str(exc))


class DocumentRow(QWidget):
    def __init__(self, filename, on_delete):
        super().__init__()
        self.filename = filename
        self.on_delete = on_delete

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        label = QLabel(filename)
        label.setWordWrap(True)
        layout.addWidget(label, 1)

        btn = QPushButton("Delete")
        btn.setObjectName("secondary")
        btn.clicked.connect(lambda: self.on_delete(self.filename))
        layout.addWidget(btn)


class DocumentsPage(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.thread = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 35, 50, 35)

        header = QHBoxLayout()
        title_box = QVBoxLayout()

        title = QLabel("Documents")
        title.setObjectName("title")
        subtitle = QLabel("Upload PDF files to build your local RAG knowledge base.")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        upload = QPushButton("+  Upload PDF")
        upload.setObjectName("primary")
        upload.clicked.connect(self.select_pdf)

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(upload)
        layout.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        self.files = QListWidget()
        self.files.setStyleSheet(
            "QListWidget { background: transparent; border: none; }"
            "QListWidget::item { padding: 0; border-bottom: 1px solid #292c33; }"
        )
        card_layout.addWidget(self.files)

        self.hint = QLabel(
            "Loaded documents are indexed for RAG. Delete any file if you want to remove it from the assistant's knowledge base."
        )
        self.hint.setObjectName("subtitle")
        self.hint.setWordWrap(True)
        card_layout.addWidget(self.hint)

        layout.addWidget(card, 1)

        self.load_documents()

    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF",
            "",
            "PDF files (*.pdf)"
        )

        if not path:
            return

        self._start_upload(path)

    def load_documents(self):
        self.files.clear()
        try:
            data = self.client.list_documents()
            documents = data.get("documents", [])
        except Exception as exc:
            self.files.addItem(f"✕  Unable to load documents: {exc}")
            return

        if not documents:
            self.files.addItem("No documents uploaded yet.")
            return

        for filename in documents:
            item = QListWidgetItem(self.files)
            row = DocumentRow(filename, self.delete_document)
            item.setSizeHint(row.sizeHint())
            self.files.setItemWidget(item, row)

    def _start_upload(self, path):
        self.files.clear()
        self.files.addItem(f"⏳  Uploading: {path.split('/')[-1]}")
        self.worker = UploadWorker(self.client, path)
        self.thread = QThread()

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.upload_finished)
        self.worker.error.connect(self.upload_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup)

        self.thread.start()

    def _start_delete(self, filename):
        self.worker = DeleteWorker(self.client, filename)
        self.thread = QThread()

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.delete_finished)
        self.worker.error.connect(self.delete_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup)

        self.thread.start()

    def upload_finished(self, message, documents):
        self.load_documents()

    def upload_error(self, message):
        self.files.clear()
        self.files.addItem(f"✕  Upload failed: {message}")

    def delete_document(self, filename):
        answer = QMessageBox.question(
            self,
            "Remove document",
            f"Delete '{filename}' from the local RAG knowledge base?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._start_delete(filename)

    def delete_finished(self, documents):
        self.load_documents()

    def delete_error(self, message):
        self.files.clear()
        self.files.addItem(f"✕  Delete failed: {message}")

    def cleanup(self):
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
