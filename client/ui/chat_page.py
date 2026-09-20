from pathlib import Path
import json
import re

from PySide6.QtCore import QEvent, QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QTextBrowser
)


class StreamWorker(QObject):
    token = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, client, question, pdf_mode=True):
        super().__init__()
        self.client = client
        self.question = question
        self.pdf_mode = pdf_mode

    def run(self):
        try:
            if self.pdf_mode:
                try:
                    stream = self.client.stream_pdf_chat(self.question)
                except Exception:
                    stream = self.client.stream_chat(self.question)
                    self.pdf_mode = False
            else:
                stream = self.client.stream_chat(self.question)

            for part in stream:
                self.token.emit(part)
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))


class ChatPage(QWidget):
    def __init__(self, client, mode="general"):
        super().__init__()
        self.client = client
        self.thread = None
        self.worker = None
        self.history_path = Path(__file__).resolve().parents[2] / "data" / "chat_history.json"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        self.sessions = self._load_history()
        if not self.sessions:
            self.sessions = [{"title": "New chat", "messages": []}]

        self.current_chat = 0
        self.chat_mode = mode if mode in {"general", "documents"} else "general"
        if self.chat_mode == "documents" and not self._has_documents():
            self.chat_mode = "general"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)

        self.new_chat_button = QPushButton("+ New chat")
        self.new_chat_button.setObjectName("primary")
        self.new_chat_button.clicked.connect(self.create_new_chat)
        sidebar_layout.addWidget(self.new_chat_button)

        self.delete_chat_button = QPushButton("Delete chat")
        self.delete_chat_button.setObjectName("secondary")
        self.delete_chat_button.clicked.connect(self.delete_current_chat)
        sidebar_layout.addWidget(self.delete_chat_button)

        self.chat_list = QListWidget()
        self.chat_list.setMinimumWidth(220)
        self.chat_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; color: #e5e7eb; }"
            "QListWidget::item { padding: 10px 8px; border-radius: 8px; margin-bottom: 6px; }"
            "QListWidget::item:selected { background: #2b2f38; color: white; }"
        )
        self.chat_list.itemClicked.connect(self.select_chat)
        sidebar_layout.addWidget(self.chat_list, 1)

        main_panel = QVBoxLayout()
        title = QLabel("AI Chat")
        title.setObjectName("title")
        subtitle = QLabel("Ask questions about your indexed PDF knowledge base.")
        subtitle.setObjectName("subtitle")
        main_panel.addWidget(title)
        main_panel.addWidget(subtitle)

        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(False)
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet(
            "QTextBrowser { background: transparent; border: 1px solid #292c33; border-radius: 12px; padding: 18px; color: white; }"
        )
        main_panel.addWidget(self.chat_view, 1)

        composer = QHBoxLayout()
        self.input = QTextEdit()
        self.input.setPlaceholderText("Ask something about your documents...")
        self.input.setFixedHeight(82)
        self.input.installEventFilter(self)

        self.send_button = QPushButton("Send  ➤")
        self.send_button.setObjectName("primary")
        self.send_button.setFixedWidth(120)
        self.send_button.clicked.connect(self.send)

        composer.addWidget(self.input, 1)
        composer.addWidget(self.send_button)
        main_panel.addLayout(composer)

        layout.addWidget(sidebar)
        layout.addLayout(main_panel, 1)

        self._populate_chat_list()
        self.render_chat()

    def _load_history(self):
        if not self.history_path.exists():
            return []
        try:
            with self.history_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def _save_history(self):
        with self.history_path.open("w", encoding="utf-8") as file:
            json.dump(self.sessions, file, ensure_ascii=False, indent=2)

    def _populate_chat_list(self):
        self.chat_list.clear()
        for idx, session in enumerate(self.sessions):
            title = session.get("title") or "New chat"
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.chat_list.addItem(item)

        if self.sessions:
            self.chat_list.setCurrentRow(self.current_chat)

    def create_new_chat(self):
        if self.worker is not None:
            return

        self.sessions.append({"title": "New chat", "messages": []})
        self.current_chat = len(self.sessions) - 1
        self._populate_chat_list()
        self.render_chat()
        self._save_history()

    def delete_current_chat(self):
        if not self.sessions:
            return
        if len(self.sessions) == 1:
            self.sessions[0] = {"title": "New chat", "messages": []}
            self.current_chat = 0
        else:
            del self.sessions[self.current_chat]
            self.current_chat = max(0, min(self.current_chat, len(self.sessions) - 1))

        self._populate_chat_list()
        self.render_chat()
        self._save_history()

    def select_chat(self, item):
        if self.worker is not None:
            return

        self.current_chat = int(item.data(Qt.ItemDataRole.UserRole))
        self.render_chat()

    def render_chat(self):
        if not self.sessions or not (0 <= self.current_chat < len(self.sessions)):
            return

        session = self.sessions[self.current_chat]
        messages = session.get("messages", [])
        html = ""
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            sources = message.get("sources", [])

            display = self._markdown_to_html(content)
            source_block = ""
            if role == "assistant" and sources:
                clean = ", ".join(str(item).strip() for item in sources if item)
                if clean:
                    source_block = (
                        "<div style='margin-top: 14px; padding: 12px 14px; border-radius: 12px; "
                        "background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.25); "
                        "color: #dbeafe; font-size: 12px; line-height: 1.5; word-break: break-word;'>"
                        "<div style='font-weight: 700; color: #93c5fd; margin-bottom: 6px;'>Sources</div>"
                        "<div style='color: #dbeafe;'>"
                        f"{self._escape_html(clean)}</div></div>"
                    )

            bubble_color = "#1f2430" if role == "user" else "#111827"
            align = "flex-end" if role == "user" else "flex-start"
            label_color = "#c4b5fd" if role == "user" else "#7dd3fc"
            margin = "18px 0" if role == "assistant" else "12px 0"

            html += (
                "<div style='margin: " + margin + "; display: flex; justify-content: " + align + ";'>"
                "<div style='max-width: 82%;'>"
                "<div style='margin-bottom: 6px; color: " + label_color + "; font-size: 12px; font-weight: 700; letter-spacing: 0.3px;'>"
                + ("You" if role == "user" else "AI") + "</div>"
                "<div data-role='content' style='padding: 16px 18px; border-radius: 16px; "
                "background: " + bubble_color + "; border: 1px solid #2d3748; "
                "box-shadow: inset 0 1px 0 rgba(255,255,255,0.02); color: #f3f4f6; line-height: 1.65;'>"
                + display + "</div>"
                + source_block + "</div></div>"
            )

        self.chat_view.setHtml(
            "<style>body { font-family: 'Segoe UI', sans-serif; background: transparent; color: white; } "
            "p { margin: 0 0 12px 0; line-height: 1.65; } "
            "ul, ol { margin: 8px 0 12px 22px; padding: 0; } "
            "li { margin: 6px 0; line-height: 1.6; } "
            "b { color: #f8fafc; } "
            "i { color: #e2e8f0; } "
            "a { color: #93c5fd; }</style>"
            f"<body>{html}</body>"
        )
        self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())

    def _markdown_to_html(self, text):
        if not text:
            return "&nbsp;"

        text = self._escape_html(text)
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return "&nbsp;"

        text = re.sub(r"\n\s*\n+", "\n\n", text)
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        rendered = []

        for part in paragraphs:
            lines = [line.strip() for line in part.split("\n") if line.strip()]
            if not lines:
                continue

            bullet_lines = [line for line in lines if re.match(r"^[-*]\s+", line)]
            number_lines = [line for line in lines if re.match(r"^\d+\.\s+", line)]

            if bullet_lines and len(bullet_lines) == len(lines):
                items = [re.sub(r"^[-*]\s+", "", line) for line in lines]
                rendered.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
                continue

            if number_lines and len(number_lines) == len(lines):
                items = [re.sub(r"^\d+\.\s+", "", line) for line in lines]
                rendered.append("<ol>" + "".join(f"<li>{item}</li>" for item in items) + "</ol>")
                continue

            content = "<br>".join(lines)
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
            content = re.sub(r"\*(.+?)\*", r"<i>\1</i>", content)
            rendered.append(f"<p>{content}</p>")

        return "".join(rendered) if rendered else "&nbsp;"

    def _escape_html(self, text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _has_documents(self):
        try:
            data = self.client.list_documents()
            return bool(data.get("documents"))
        except Exception:
            return False

    def send(self):
        if self.worker is not None:
            return

        question = self.input.toPlainText().strip()
        if not question:
            return

        session = self.sessions[self.current_chat]
        session.setdefault("messages", [])
        session["messages"].append({"role": "user", "content": question})

        if len(session["messages"]) == 1:
            session["title"] = question[:30].strip() + ("..." if len(question) > 30 else "")

        session["messages"].append({"role": "assistant", "content": "", "sources": []})
        self.input.clear()
        self.send_button.setEnabled(False)
        self._save_history()
        self.render_chat()

        self.thread = QThread()
        use_pdf = self.chat_mode == "documents" and self._has_documents()
        self.worker = StreamWorker(self.client, question, pdf_mode=use_pdf)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.token.connect(self.append_token)
        self.worker.finished.connect(self.stream_finished)
        self.worker.error.connect(self.stream_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup)
        self.thread.start()

    def eventFilter(self, watched, event):
        if watched is self.input and event.type() == QEvent.Type.KeyPress:
            is_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            has_shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            if is_enter and not has_shift:
                self.send()
                return True

        return super().eventFilter(watched, event)

    def append_token(self, token):
        if not self.sessions or not (0 <= self.current_chat < len(self.sessions)):
            return

        session = self.sessions[self.current_chat]
        messages = session.get("messages", [])
        if not messages or messages[-1].get("role") != "assistant":
            messages.append({"role": "assistant", "content": "", "sources": []})

        assistant = messages[-1]
        assistant["content"] += token

        if "Sources:" in assistant["content"]:
            before, _, after = assistant["content"].rpartition("Sources:")
            assistant["content"] = before.strip()
            assistant["sources"] = [item.strip() for item in after.split(",") if item.strip()]
        elif "Sources" in assistant["content"] and not assistant.get("sources"):
            before, _, after = assistant["content"].rpartition("Sources")
            assistant["content"] = before.strip()
            assistant["sources"] = [item.strip() for item in after.split(",") if item.strip()]

        self.render_chat()

    def stream_finished(self):
        self.send_button.setEnabled(True)
        self._save_history()

    def stream_error(self, message):
        if not self.sessions or not (0 <= self.current_chat < len(self.sessions)):
            return
        session = self.sessions[self.current_chat]
        messages = session.get("messages", [])
        if messages and messages[-1].get("role") == "assistant":
            messages[-1]["content"] = f"Error: {message}"
            messages[-1]["sources"] = []
        self.render_chat()
        self.send_button.setEnabled(True)
        self._save_history()

    def cleanup(self):
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
        self._save_history()

