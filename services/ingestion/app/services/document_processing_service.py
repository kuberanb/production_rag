
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

    extracted_pages = await asyncio.to_thread(
        extract
    )

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
):
    """
    Process an uploaded document.
    """

    await connect_to_database()

    try:

        # 1. Convert document ID
        document_uuid = UUID(document_id)

        # 2. Retrieve document
        document = await get_document_by_id(
            document_uuid
        )

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        # 3. Update document status
        await update_document_status(
            document_uuid,
            "processing",
        )

        # 4. Get stored PDF path from database
        file_path = Path(
            document["file_path"]
        )

        if not file_path.is_file():
            raise FileNotFoundError(
                f"PDF file not found: {file_path}"
            )

        # 5. Extract PDF text page by page
        extracted_pages = await extract_pdf_text(
            str(file_path)
        )

        # 6. Calculate extraction statistics
        total_pages = len(extracted_pages)

        total_characters = sum(
            len(page["text"])
            for page in extracted_pages
        )

        print(
            f"Document {document_id}: "
            f"Extracted {total_characters} characters "
            f"from {total_pages} pages"
        )

        # 7. Temporary extraction result
        return extracted_pages

    except Exception as exc:

        # Update document status when processing fails
        try:
            await update_document_status(
                UUID(document_id),
                "failed",
                str(exc)[:1000],
            )

        except Exception as status_error:
            print(
                f"Failed to update document status: "
                f"{status_error}"
            )

        raise

    finally:

        # 8. Close worker database pool
        await close_database_connection()
