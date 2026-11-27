
import asyncio
from pathlib import Path
from uuid import UUID

import fitz

from shared.database import (
    connect_to_database,
    close_database_connection,
)

from services.ingestion.app.repositories.document_repository import (
    get_document_by_id,
    update_document_status,
)

from services.ingestion.app.repositories.chunk_repsository import (
    insert_document_chunks,
)

from services.ingestion.app.services.chunking_service import (
    chunk_text,
)

from services.ingestion.app.services.embedding_service import (
    generate_embedding as generate_embeddings,
)


async def extract_pdf_text(
    file_path: str
) -> list[dict[str, int | str]]:
    """
    Extract text from a PDF page by page.
    Preserve original page numbers.
    """

    def extract():
        pages = []

        with fitz.open(file_path) as document:

            if document.is_encrypted:
                raise ValueError(
                    "Encrypted PDF files are not supported"
                )

            for page_number, page in enumerate(
                document,
                start=1
            ):
                text = page.get_text(
                    "text",
                    sort=True
                ).strip()

                pages.append({
                    "page_number": page_number,
                    "text": text
                })

        return pages

    extracted_pages = await asyncio.to_thread(extract)

    if not any(
        page["text"]
        for page in extracted_pages
    ):
        raise ValueError(
            "No extractable text found in PDF. "
            "The PDF may contain scanned images."
        )

    return extracted_pages


async def process_document_async(
    document_id: str
) -> int:
    """
    Process an uploaded PDF.

    Extraction -> Chunking -> Embeddings -> Database insertion.
    """

    document_uuid = UUID(document_id)

    database_connected = False

    try:
        # 1. Connect to PostgreSQL
        await connect_to_database()
        database_connected = True

        # 2. Retrieve document
        document = await get_document_by_id(
            document_uuid
        )

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        # 3. Update status
        await update_document_status(
            document_uuid,
            "processing",
            error_message=None,
        )

        # 4. Validate PDF file
        file_path = Path(document["file_path"])

        if not file_path.is_file():
            raise FileNotFoundError(
                f"PDF file not found: {file_path}"
            )

        # 5. Extract PDF text
        extracted_pages = await extract_pdf_text(
            str(file_path)
        )

        print(
            f"Extracted text from "
            f"{len(extracted_pages)} pages"
        )

        # 6. Generate chunks
        chunks = chunk_text(extracted_pages)

        if not chunks:
            raise ValueError(
                "No chunks were generated from the PDF"
            )

        print(
            f"Generated {len(chunks)} chunks"
        )

        # 7. Prepare chunk texts
        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        # 8. Generate embeddings
        embeddings = await generate_embeddings(texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count"
            )

        print(
            f"Generated {len(embeddings)} embeddings"
        )

        # 9. Insert chunks and embeddings
        inserted_count = await insert_document_chunks(
            document_uuid,
            chunks,
            embeddings,
        )

        # 10. Mark document as completed
        await update_document_status(
            document_uuid,
            "completed",
            error_message=None,
            chunk_count=inserted_count,
        )

        print(
            f"Document {document_id} processed successfully. "
            f"Inserted {inserted_count} chunks."
        )

        return inserted_count

    except Exception:
        # Let Celery handle retries and final failure status.
        raise

    finally:
        if database_connected:
            await close_database_connection()
