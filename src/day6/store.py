"""Persistent exact cosine retrieval with PostgreSQL and pgvector."""
from math import isfinite
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import Chunk


def _vector(values: list[float], dimensions: int) -> str:
    if len(values) != dimensions or not all(isfinite(value) for value in values):
        raise ValueError(f"Expected {dimensions} finite embedding values")
    return "[" + ",".join(str(float(value)) for value in values) + "]"


class PgVectorStore:
    """One table holds all strategies; each run synchronizes its strategy rows."""

    def __init__(self, database_url: str, dimensions: int, model_name: str) -> None:
        if not database_url or dimensions <= 0:
            raise ValueError("DATABASE_URL and positive dimensions are required")
        self.database_url = database_url
        self.dimensions = dimensions
        self.model_name = model_name

    def create_schema(self) -> None:
        # The dimension is checked above and is the only interpolated SQL value.
        with psycopg.connect(self.database_url) as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            connection.execute(f"""
                CREATE TABLE IF NOT EXISTS starter_chunks (
                    strategy text NOT NULL,
                    chunk_id text NOT NULL,
                    document_id text NOT NULL,
                    source text NOT NULL,
                    page integer NOT NULL,
                    content text NOT NULL,
                    metadata jsonb NOT NULL,
                    model_name text NOT NULL,
                    embedding vector({self.dimensions}) NOT NULL,
                    PRIMARY KEY (strategy, chunk_id)
                )
            """)
            connection.execute("CREATE INDEX IF NOT EXISTS starter_chunks_doc_idx ON starter_chunks (strategy, document_id)")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and embedding counts differ")
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs")
        ids = [chunk.chunk_id for chunk in chunks]
        with psycopg.connect(self.database_url) as connection:
            for chunk, vector in zip(chunks, vectors):
                connection.execute("""
                    INSERT INTO starter_chunks
                      (strategy, chunk_id, document_id, source, page, content, metadata, model_name, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                    ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                      document_id = EXCLUDED.document_id,
                      source = EXCLUDED.source,
                      page = EXCLUDED.page,
                      content = EXCLUDED.content,
                      metadata = EXCLUDED.metadata,
                      model_name = EXCLUDED.model_name,
                      embedding = EXCLUDED.embedding
                """, (strategy, chunk.chunk_id, chunk.document_id, chunk.source,
                      chunk.page, chunk.text, Jsonb(chunk.metadata), self.model_name,
                      _vector(vector, self.dimensions)))
            # Removes chunks of changed or removed documents in the same transaction.
            connection.execute(
                "DELETE FROM starter_chunks WHERE strategy = %s AND NOT (chunk_id = ANY(%s))",
                (strategy, ids),
            )

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        allowed = {"document_id", "source", "page", "category", "year", "language"}
        filters = filters or {}
        unknown = set(filters) - allowed
        if unknown:
            raise ValueError(f"Unsupported metadata filters: {sorted(unknown)}")
        vector = _vector(query_vector, self.dimensions)
        clauses = ["strategy = %s", "model_name = %s"]
        params: list[Any] = [strategy, self.model_name]
        for key, value in filters.items():
            if key in {"document_id", "source", "page"}:
                clauses.append(f"{key} = %s")
                params.append(value)
            else:
                clauses.append(f"metadata ->> '{key}' = %s")
                params.append(str(value))
        query = f"""
            SELECT chunk_id, document_id, source, page, content, metadata,
                   1 - (embedding <=> %s::vector) AS score
            FROM starter_chunks
            WHERE {' AND '.join(clauses)}
            ORDER BY embedding <=> %s::vector, chunk_id
            LIMIT %s
        """
        with psycopg.connect(self.database_url) as connection:
            rows = connection.execute(query, (vector, *params, vector, top_k)).fetchall()
        return [dict(chunk_id=row[0], document_id=row[1], source=row[2],
                     page=row[3], text=row[4], metadata=row[5], score=float(row[6]))
                for row in rows]
