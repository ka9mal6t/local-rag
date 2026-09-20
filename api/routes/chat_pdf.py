from flask import Blueprint, Response, jsonify, request, stream_with_context
from api.services.rag import generate_answer_stream


chat_pdf = Blueprint("chat_pdf", __name__)


@chat_pdf.route("/chat_pdf", methods=["POST"])
def ai_chat_pdf():
    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    answer_stream = generate_answer_stream(question)
    try:
        first_chunk = next(answer_stream)
    except StopIteration:
        return jsonify({"error": "The model returned an empty response"}), 502
    except Exception:
        return jsonify({"error": "Unable to connect to the Ollama model service"}), 503

    def stream_response():
        yield first_chunk
        yield from answer_stream

    return Response(
        stream_with_context(stream_response()),
        content_type="text/event-stream"
    )
