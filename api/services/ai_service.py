from flask import current_app
from api.config import ai_model


def generate_response(messages):
    response = current_app.client.chat(
        model=ai_model,
        messages=messages,
        options={"temperature": 0.3}
    )
    return response["message"]["content"]


def generate_response_stream(messages):
    stream = current_app.client.chat(
        model=ai_model,
        messages=messages,
        options={"temperature": 0.3},
        stream=True
    )

    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield content


def summarize_messages(messages, summary):
    text_block = f"system: {summary}\n" + "\n".join(
        [f"{m.role}: {m.content}" for m in messages]
    )

    response = current_app.client.chat(
        model=ai_model,
        messages=[
            {
                "role": "system",
                "content": "Summarize the conversation keeping key technical details."
            },
            {
                "role": "user",
                "content": text_block
            }
        ],
        options={"temperature": 0.2}
    )

    return response["message"]["content"]