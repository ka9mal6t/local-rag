from flask import request, jsonify, Blueprint
import os
from flask import current_app
from app.services.static_service import get_static_files_paths

upload_pdf = Blueprint("upload-pdf", __name__)


@upload_pdf.route("/upload-pdf", methods=["POST"])
def upload_ai_pdf():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file"}), 400

    if file.content_type != "application/pdf":
        return jsonify({"error": "File is not a PDF"}), 400

    filepath = os.path.join(current_app.root_path, "static", "pdf", file.filename)
    file.save(filepath)

    current_app.app_rag.add_document(current_app.root_path, filepath)

    return jsonify({"message": "PDF uploaded and processed"})