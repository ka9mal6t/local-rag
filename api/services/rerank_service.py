from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(question, chunks, top_n=8):
    pairs = [(question, chunk["text"]) for chunk in chunks]

    scores = model.predict(pairs)

    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return [
        {**chunk, "rerank_score": float(score)}
        for chunk, score in scored_chunks[:top_n]
    ]