from flask import Blueprint, request, jsonify
from app.services.rag import generate_answer
from app.logs import Log
from app.config import *

ask_pdf = Blueprint("ask_pdf", __name__)


@ask_pdf.route("/ask_pdf", methods=["POST"])
def ai_ask_pdf():
    logger = Log.get("ask_pdf")
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    result = generate_answer(question)

    if result.get("answer") == fail_pdf_search:
        logger.info("❌ Answer didn't found | "
                    f"sources: {result['sources']}")
    else:
        logger.info("✅ Answer was founding | "
                    f"sources: {result['sources']}")

    return jsonify({
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"]
    })