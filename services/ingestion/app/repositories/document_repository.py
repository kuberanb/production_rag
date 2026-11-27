
import asyncpg
from uuid import UUID

from shared.database import get_pool

async def create_document(
        filename:str,
        file_path:str
) -> asyncpg.Record:

    pool = await get_pool()

    query = """
        INSERT INTO documents (
            filename,
            file_path,
            status
        )
        VALUES ($1, $2, $3)
        RETURNING
            id,
            filename,
            file_path,
            status,
            created_at;
    """

    async with pool.acquire() as connection:
        document = await connection.fetchrow(
            query,
            filename,
            file_path,
            "pending",
        )

        return document

async def get_document_by_id(document_id:UUID)->asyncpg.Record | None:

    pool = await get_pool()

    query = """
        SELECT
            id,
            filename,
            file_path,
            status,
            error_message,
            chunk_count,
            created_at,
            updated_at
        FROM documents
        WHERE id = $1;
    """

    async with pool.acquire() as connection:
        document = await connection.fetchrow(query,document_id)

        return document

async def update_document_status(
    document_id: UUID,
    status: str,
    error_message: str | None = None,
    chunk_count: int | None = None,
) -> asyncpg.Record | None:

    pool = await get_pool()

    query = """
        UPDATE documents
        SET
            status = $2,
            error_message = $3,
            chunk_count = COALESCE($4, chunk_count),
            updated_at = NOW()
        WHERE id = $1
        RETURNING
            id,
            status,
            error_message,
            chunk_count;
    """

    async with pool.acquire() as connection:
        document = await connection.fetchrow(
            query,
            document_id,
            status,
            error_message,
            chunk_count,
        )

        return document


async def delete_document_by_id(
    document_id: UUID,
) -> asyncpg.Record | None:

    pool = await get_pool()

    query = """
        DELETE FROM documents
        WHERE id = $1
          AND status <> 'processing'
        RETURNING
            id,
            filename,
            file_path,
            status;
    """

    async with pool.acquire() as connection:
        document = await connection.fetchrow(
            query,
            document_id,
        )

        return document
    
