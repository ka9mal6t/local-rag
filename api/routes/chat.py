from flask import Blueprint, Response, stream_with_context, request
from flask import Blueprint, request, jsonify
from ..database import db
from ..models.chat import Chat
from ..models.message import Message
from ..services.ai_service import generate_response_stream, summarize_messages

chat = Blueprint("chat", __name__)


@chat.route("/chat", methods=["POST"])
def ai_chat():
    data = request.json
    chat_id = data.get("chat_id")
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    if not chat_id:
        chat = Chat()
        chat_id = chat.id
        db.session.add(chat)
        db.session.commit()
    elif not Chat.query.get(chat_id):
        chat = Chat(id=chat_id)
        db.session.add(chat)
        db.session.commit()

    messages_count = Message.query.filter_by(chat_id=chat_id).count()

    formatted = [{"role": "system", "content": "You are a technical assistant."}]

    if messages_count >= 10:
        old_messages = (
            Message.query
            .filter_by(chat_id=chat_id)
            .order_by(Message.id)
            .all()
        )
        chat: Chat = Chat.query.get(chat_id)

        summary_text = summarize_messages(old_messages, chat.summary)

        chat.summary = summary_text

        for msg in old_messages:
            db.session.delete(msg)

        db.session.commit()

        formatted.append({"role": "system",
                          "content": f"Conversation summary: {chat.summary}"})

    else:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(
            Message.id.desc()).limit(10).all()

        messages = list(reversed(messages))

        formatted += [{"role": m.role, "content": m.content} for m in messages]

    user_message = Message(chat_id=chat_id, role="user", content=question)
    db.session.add(user_message)
    db.session.commit()

    formatted.append({"role": "user",
                      "content": user_message.content})

    def generate():

        full_answer = ""

        for token in generate_response_stream(formatted):
            full_answer += token
            yield f"data: {token}\n\n"

        # Save after generation
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content=full_answer
        )

        db.session.add(assistant_message)
        db.session.commit()

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream"
    )