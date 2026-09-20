from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame
)

from client.services.api_client import ApiClient
from client.ui.chat_page import ChatPage
from client.ui.documents_page import DocumentsPage
from client.ui.settings_page import SettingsPage


STYLE = """
QMainWindow, QWidget {
    background: #101114;
    color: #f2f3f5;
    font-family: Segoe UI;
    font-size: 14px;
}

QFrame#sidebar {
    background: #17191e;
    border-right: 1px solid #292c33;
}

QLabel#logo {
    font-size: 22px;
    font-weight: 700;
    padding: 8px 4px 20px 4px;
}

QPushButton#navButton {
    text-align: left;
    padding: 12px 14px;
    border: none;
    border-radius: 8px;
    color: #aeb4bf;
    background: transparent;
}

QPushButton#navButton:hover {
    background: #22252c;
    color: white;
}

QPushButton#navButton:checked {
    background: #2b2f38;
    color: white;
}

QLabel#title {
    font-size: 26px;
    font-weight: 700;
}

QLabel#subtitle {
    color: #8d94a1;
}

QFrame#card {
    background: #181a20;
    border: 1px solid #292c33;
    border-radius: 12px;
}

QLineEdit, QTextEdit {
    background: #181a20;
    border: 1px solid #30343c;
    border-radius: 9px;
    padding: 10px;
    color: white;
}

QPushButton#primary {
    background: #e7e9ed;
    color: #101114;
    border: none;
    border-radius: 9px;
    padding: 10px 16px;
    font-weight: 600;
}

QPushButton#primary:hover {
    background: #ffffff;
}

QPushButton#secondary {
    background: #22252c;
    color: #e5e7eb;
    border: 1px solid #30343c;
    border-radius: 9px;
    padding: 10px 16px;
}

QPushButton#secondary:hover {
    background: #2a2e36;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local RAG")
        self.resize(1200, 760)
        self.setStyleSheet(STYLE)

        self.client = ApiClient()

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)

        logo = QLabel("◈  Local RAG")
        logo.setObjectName("logo")
        side.addWidget(logo)

        self.buttons = []
        for text, index in [
            ("⌂  Dashboard", 0),
            ("▣  Documents", 1),
            ("◉  General chat", 2),
            ("📚  Document chat", 3),
            ("⚙  Settings", 4),
        ]:
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.show_page(i))
            side.addWidget(button)
            self.buttons.append(button)

        side.addStretch()
        version = QLabel("Local RAG • local AI")
        version.setObjectName("subtitle")
        side.addWidget(version)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard())
        self.documents = DocumentsPage(self.client)
        self.general_chat = ChatPage(self.client, mode="general")
        self.chat = ChatPage(self.client, mode="documents")
        self.settings = SettingsPage(self.client)
        self.stack.addWidget(self.documents)
        self.stack.addWidget(self.general_chat)
        self.stack.addWidget(self.chat)
        self.stack.addWidget(self.settings)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack)

        self.show_page(0)

    def dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(42, 38, 42, 38)
        layout.setSpacing(20)

        title = QLabel("Welcome to Local RAG")
        title.setObjectName("title")
        subtitle = QLabel(
            "Ask questions about your local PDF documents using retrieval-augmented generation."
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        for value, label in [
            ("PDF", "Document source"),
            ("FAISS", "Vector search"),
            ("Ollama", "Local LLM"),
        ]:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            value_label = QLabel(value)
            value_label.setObjectName("title")
            label_widget = QLabel(label)
            label_widget.setObjectName("subtitle")
            card_layout.addWidget(value_label)
            card_layout.addWidget(label_widget)
            cards.addWidget(card)

        layout.addLayout(cards)

        info = QFrame()
        info.setObjectName("card")
        info_layout = QVBoxLayout(info)
        heading = QLabel("How it works")
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        flow = QLabel(
            "PDF → text extraction → chunks → embeddings + keyword search → "
            "reranking → Ollama → answer"
        )
        flow.setObjectName("subtitle")
        flow.setWordWrap(True)
        info_layout.addWidget(heading)
        info_layout.addWidget(flow)
        layout.addWidget(info)
        layout.addStretch()

        return page

    def show_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
