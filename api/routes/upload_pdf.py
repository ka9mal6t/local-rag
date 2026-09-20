from flask import request, jsonify, Blueprint
import os
from flask import current_app
from urllib.parse import unquote

upload_pdf = Blueprint("upload-pdf", __name__)


@upload_pdf.route("/documents", methods=["GET"])
def list_documents():
    return jsonify({
        "documents": current_app.app_rag.list_documents()
    })


@upload_pdf.route("/documents/<path:filename>", methods=["DELETE"])
def delete_document(filename):
    filename = unquote(filename)
    deleted = current_app.app_rag.delete_document(current_app.root_path, filename)

    if not deleted:
        return jsonify({"error": "Document not found"}), 404

    return jsonify({
        "message": f"Document '{filename}' removed",
        "documents": current_app.app_rag.list_documents()
    })


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

    return jsonify({
        "message": "PDF uploaded and processed",
        "documents": current_app.app_rag.list_documents()
    })