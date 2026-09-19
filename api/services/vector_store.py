import faiss
import numpy as np
import pickle
import os


class VectorStore:
    def __init__(self, path, dimension=None):
        self.path = path
        self.index_path = os.path.join(self.path, os.path.join(
            "vector_index", "faiss.index"))
        self.metadata_path = os.path.join(self.path, os.path.join(
            "vector_index", "metadata.pkl"))
        self.texts = []
        self.metadata = []

        if os.path.exists(self.index_path):
            self.load()
        else:
            if dimension is None:
                raise ValueError("Dimension required to create new index")
            self.index = faiss.IndexFlatIP(dimension)

    def add(self, embeddings, texts, metadata):
        self.index.add(np.array(embeddings).astype("float32"))
        self.texts.extend(texts)
        self.metadata.extend(metadata)

    def search(self, query_embedding):
        k = min(15, len(self.texts))
        D, I = self.index.search(
            np.array([query_embedding]).astype("float32"), k)

        results = []

        for idx in I[0]:
            if idx < len(self.texts):
                results.append({
                    "text": self.texts[idx],
                    "metadata": self.metadata[idx]})
        return results

    def save(self):
        os.makedirs(os.path.join(self.path, "vector_index"), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump({
                "texts": self.texts,
                "metadata": self.metadata}, f)

    def load(self):
        self.index = faiss.read_index(self.index_path)

        with open(self.metadata_path, "rb") as f:
            data = pickle.load(f)

        self.texts = data["texts"]
        self.metadata = data["metadata"]