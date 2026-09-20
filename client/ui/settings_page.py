from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton


class SettingsPage(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client

        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 32, 42, 28)

        title = QLabel("Settings")
        title.setObjectName("title")
        subtitle = QLabel("Configure the connection used by the desktop client.")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        row = QHBoxLayout()
        label = QLabel("API URL")
        self.url = QLineEdit(client.base_url)
        save = QPushButton("Save")
        save.setObjectName("primary")
        save.clicked.connect(self.save)

        row.addWidget(label)
        row.addWidget(self.url, 1)
        row.addWidget(save)
        layout.addLayout(row)

        note = QLabel(
            "Default: http://127.0.0.1:5000. "
            "If Flask runs in Docker, use the host/port exposed by your compose configuration."
        )
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def save(self):
        self.client.base_url = self.url.text().strip().rstrip("/")
