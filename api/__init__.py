from flask import Flask
from api.services.rag_service import RAGService
from api.services.static_service import get_static_files_paths
from database import db
from .route import main
from ollama import Client

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"

    app.client = Client(host="http://ollama:11434")
    db.init_app(app)

    pdf_files_path = get_static_files_paths(app.root_path, ".pdf", "pdf")
    app.app_rag = RAGService(app.root_path, pdf_files_path)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main)

    return app