from flask import Blueprint, Response, stream_with_context, request
from api.services.rag import generate_answer_stream


chat_pdf = Blueprint("chat_pdf", __name__)


@chat_pdf.route("/chat_pdf", methods=["POST"])
def ai_chat_pdf():

    data = request.json
    question = data.get("question")

    return Response(
        stream_with_context(generate_answer_stream(question)),
        content_type="text/event-stream"
    )