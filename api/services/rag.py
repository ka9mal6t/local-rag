from flask import current_app


def generate_answer(question):
    rag = current_app.app_rag
    results = rag.retrieve(question)

    context_chunks = []
    sources = set()

    for item in results:
        context_chunks.append(item["text"])
        sources.add(item["metadata"]["source"])

    context = "\n\n".join(context_chunks)

    response = current_app.client.chat(
        model=ai_model,
        messages=[
            {
                "role": "system",
                "content":
                    """
                    You are an assistant answering questions based strictly on provided context.
                    If the answer is not in the context, say:
                    "I cannot find the answer in the document."
                    Be clear and structured.
                    """
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ],
        options={"temperature": 0.2}
    )

    answer = response["message"]["content"]

    return {
        "answer": answer,
        "sources": list(sources)
    }


def generate_answer_stream(question):
    rag = current_app.app_rag
    results = rag.retrieve(question)

    context_chunks = []
    sources = set()

    for item in results:
        context_chunks.append(item["text"])
        sources.add(item["metadata"]["source"])

    context = "\n\n".join(context_chunks)

    stream = current_app.client.chat(
        model=ai_model,
        messages=[
            {
                "role": "system",
                "content": """
               You are an assistant answering questions based strictly on provided context.
                If the answer is not in the context, say:
                "I cannot find the answer in the document."
                Be clear and structured.
                """
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ],
        options={"temperature": 0.2},
        stream=True
    )

    for chunk in stream:
        content = chunk["message"]["content"]
        if content:
            yield f"data: {content}\n\n"