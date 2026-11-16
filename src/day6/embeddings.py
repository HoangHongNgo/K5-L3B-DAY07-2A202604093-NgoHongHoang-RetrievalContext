"""Local sentence-transformers embeddings for documents and queries."""
from typing import Protocol
import warnings


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Use the same model and normalization for indexing and searching."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name, local_files_only=True)
        except (FileNotFoundError, OSError):
            self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_embedding_dimension()
        if not self.dimensions:
            raise ValueError(f"Cannot determine embedding dimension for {model_name}")
        self.truncated_text_count = 0

    def _warn_if_truncated(self, texts: list[str]) -> None:
        lengths = self.model.tokenizer(
            texts, add_special_tokens=True, truncation=False, return_length=True
        )["length"]
        count = sum(length > self.model.max_seq_length for length in lengths)
        if count:
            self.truncated_text_count += count
            warnings.warn(
                f"{count} texts exceed the model's {self.model.max_seq_length}-token limit "
                "and will be truncated; reduce fixed chunk size if this affects evidence",
                stacklevel=2,
            )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._warn_if_truncated(texts)
        vectors = self.model.encode_document(texts, batch_size=32, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, question: str) -> list[float]:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        self._warn_if_truncated([question])
        vector = self.model.encode_query(question, normalize_embeddings=True)
        return vector.tolist()
