from api.services.document_loader import load_pdf, chunk_text
from api.services.embedding_service import embed_texts, embed_query
from api.services.rerank_service import rerank
from api.services.vector_store import VectorStore
from api.services.keyword_service import KeywordSearch
import os
from api.logs import Log


class RAGService:

    @staticmethod
    def _embedding_dimension():
        return len(embed_texts(["test"])[0])

    def __init__(self, path, files):
        self.logger = Log.get("pdf")
        self.path = path
        index_exists = os.path.exists(os.path.join(path, os.path.join(
            "vector_index", "faiss.index")))

        if index_exists:
            self.logger.info("Loading existing FAISS index...")
            self.store = VectorStore(path)
            self.keyword_search = KeywordSearch(self.store.texts, self.store.metadata)
            return

        self.rebuilding(path, files)

    def _rebuild_index_from_chunks(self, texts, metadata):
        faiss_index_path = os.path.join(self.path, "vector_index", "faiss.index")
        metadata_path = os.path.join(self.path, "vector_index", "metadata.pkl")

        for file_path in (faiss_index_path, metadata_path):
            if os.path.exists(file_path):
                os.remove(file_path)

        if not texts:
            dimension = self._embedding_dimension()
            self.store = VectorStore(self.path, dimension)
            self.store.save()
            self.keyword_search = KeywordSearch(self.store.texts, self.store.metadata)
            return

        embeddings = embed_texts(texts)
        dimension = len(embeddings[0])

        self.store = VectorStore(self.path, dimension)
        self.store.add(embeddings, texts, metadata)
        self.store.save()
        self.keyword_search = KeywordSearch(self.store.texts, self.store.metadata)

    def rebuilding(self, path, files):
        self.logger.info("Building new FAISS index...")

        all_chunks = []
        metadata = []

        for file in files:
            self.logger.info(f"Processing {file}")
            text = load_pdf(file)
            chunks = chunk_text(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                metadata.append({
                    "source": os.path.basename(file)
                })

        embeddings = embed_texts(all_chunks)

        self.store = VectorStore(path, len(embeddings[0]))
        self.store.add(embeddings, all_chunks, metadata)
        self.store.save()
        self.keyword_search = KeywordSearch(self.store.texts, metadata)

    def add_document(self, path, file_path):
        self.logger.info(f"Adding new file: {file_path}")

        text = load_pdf(file_path)
        chunks = chunk_text(text)

        embeddings = embed_texts(chunks)
        embedding_dimension = len(embeddings[0])

        if not hasattr(self.store, "index") or self.store.index.d != embedding_dimension:
            existing_texts = list(self.store.texts)
            existing_metadata = list(self.store.metadata)
            merged_texts = existing_texts + chunks
            merged_metadata = existing_metadata + [
                {"source": os.path.basename(file_path)}
                for _ in chunks
            ]
            self._rebuild_index_from_chunks(merged_texts, merged_metadata)
            return

        metadata = [
            {"source": os.path.basename(file_path)}
            for _ in chunks
        ]

        self.store.add(embeddings, chunks, metadata)
        self.store.save()

        # обновляем keyword search
        self.keyword_search = KeywordSearch(self.store.texts, self.store.metadata)

    def list_documents(self):
        documents = sorted({
            metadata["source"]
            for metadata in self.store.metadata
            if metadata.get("source")
        })
        return documents

    def delete_document(self, path, file_name):
        if not file_name:
            return False

        remaining_texts = []
        remaining_metadata = []

        for text, metadata in zip(self.store.texts, self.store.metadata):
            if metadata.get("source") != file_name:
                remaining_texts.append(text)
                remaining_metadata.append(metadata)

        self._rebuild_index_from_chunks(remaining_texts, remaining_metadata)

        file_path = os.path.join(path, "static", "pdf", file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        return True

    def retrieve(self, question, n=8):
        query_embedding = embed_query(question)
        # 1️⃣ Embedding search
        embedding_results = self.store.search(query_embedding)

        # 2️⃣ Keyword search
        keyword_results = self.keyword_search.search(question, k=10)

        # 3️⃣ Combine indexes
        combined_indices = set()
        for item in embedding_results:
            combined_indices.add(self.store.texts.index(item["text"]))

        for item in keyword_results:
            combined_indices.add(item["index"])

        # 4️⃣ Final chunks
        combined_chunks = []

        for idx in combined_indices:
            combined_chunks.append({
                "text": self.store.texts[idx],
                "metadata": self.store.metadata[idx]
            })

        reranked = rerank(question, combined_chunks, top_n=n)
        return reranked