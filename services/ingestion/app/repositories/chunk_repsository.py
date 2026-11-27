import json
from uuid import UUID

from shared.database import get_pool

async def insert_document_chunks(
    document_id: UUID,
    chunks: list[dict[str, int | str]],
    embeddings: list[list[float]],
) -> int:
    """
    Insert document chunks and their embeddings into PostgreSQL.

    Returns the number of inserted chunks.
    """

    if not chunks:
        raise ValueError("Cannot insert an empty chunk list")

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must match"
        )

    records = []

    for chunk, embedding in zip(chunks, embeddings):

        if len(embedding) != 1536:
            raise ValueError(
                f"Expected 1536 embedding dimensions, "
                f"received {len(embedding)}"
            )

        metadata = {
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
        }

        records.append((
            document_id,
            chunk["chunk_index"],
            chunk["text"],
            embedding,
            json.dumps(metadata),
        ))

    pool = await get_pool()

    async with pool.acquire() as connection:

        async with connection.transaction():

            # Remove previous chunks when reprocessing a document.
            await connection.execute(
                """
                DELETE FROM document_chunks
                WHERE document_id = $1
                """,
                document_id,
            )

            # Insert all chunks and embeddings.
            await connection.executemany(
                """
                INSERT INTO document_chunks (
                    document_id,
                    chunk_index,
                    content,
                    embedding,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5::jsonb)
                """,
                records,
            )

    return len(records)

