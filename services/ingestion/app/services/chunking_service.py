
import re


TARGET_CHUNK_WORDS = 375
MAX_CHUNK_WORDS = 525
MIN_CHUNK_WORDS = 75
OVERLAP_WORDS = 55


def split_into_paragraphs(text: str) -> list[str]:
    """Split extracted text into meaningful paragraphs."""

    paragraphs = re.split(r"\n\s*\n", text)

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences."""

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def split_large_sentence(
    sentence: str,
    max_words: int
) -> list[str]:
    """Fallback for sentences exceeding the maximum size."""

    words = sentence.split()

    return [
        " ".join(words[i:i + max_words])
        for i in range(0, len(words), max_words)
    ]


def prepare_units(
    extracted_pages: list[dict[str, int | str]]
) -> list[dict[str, int | str]]:
    """
    Prepare paragraph/sentence units while preserving page numbers.
    """

    units = []

    for page in extracted_pages:

        page_number = int(page["page_number"])
        page_text = str(page["text"])

        if not page_text.strip():
            continue

        for paragraph in split_into_paragraphs(page_text):

            if len(paragraph.split()) <= MAX_CHUNK_WORDS:
                units.append({
                    "text": paragraph,
                    "page_number": page_number
                })
                continue

            for sentence in split_into_sentences(paragraph):

                if len(sentence.split()) <= MAX_CHUNK_WORDS:
                    units.append({
                        "text": sentence,
                        "page_number": page_number
                    })

                else:
                    for part in split_large_sentence(
                        sentence,
                        MAX_CHUNK_WORDS
                    ):
                        units.append({
                            "text": part,
                            "page_number": page_number
                        })

    return units


def build_chunks(
    units: list[dict[str, int | str]]
) -> list[dict[str, int | str]]:
    """Combine meaningful units into chunks and preserve page ranges."""

    chunks = []

    current_units = []
    current_words = 0
    current_page_start = None
    current_page_end = None

    for unit in units:

        unit_text = str(unit["text"])
        unit_page = int(unit["page_number"])
        unit_words = len(unit_text.split())

        if not current_units:
            current_units.append(unit_text)
            current_words = unit_words
            current_page_start = unit_page
            current_page_end = unit_page
            continue

        if current_words + unit_words > TARGET_CHUNK_WORDS:

            chunks.append({
                "text": "\n\n".join(current_units),
                "page_start": current_page_start,
                "page_end": current_page_end
            })

            current_units = [unit_text]
            current_words = unit_words
            current_page_start = unit_page
            current_page_end = unit_page

        else:
            current_units.append(unit_text)
            current_words += unit_words
            current_page_end = unit_page

    if current_units:
        chunks.append({
            "text": "\n\n".join(current_units),
            "page_start": current_page_start,
            "page_end": current_page_end
        })

    # Merge a very small final chunk when possible.
    if len(chunks) > 1:

        last_words = len(
            str(chunks[-1]["text"]).split()
        )

        combined_text = (
            str(chunks[-2]["text"])
            + "\n\n"
            + str(chunks[-1]["text"])
        )

        combined_words = len(combined_text.split())

        if (
            last_words < MIN_CHUNK_WORDS
            and combined_words <= MAX_CHUNK_WORDS
        ):
            chunks[-2]["text"] = combined_text
            chunks[-2]["page_end"] = chunks[-1]["page_end"]

            chunks.pop()

    return chunks


def add_overlap(
    chunks: list[dict[str, int | str]]
) -> list[dict[str, int | str]]:
    """Add trailing words from the original previous chunk."""

    if not chunks:
        return []

    result = []

    for index, chunk in enumerate(chunks):

        current_text = str(chunk["text"])

        if index == 0:
            result.append({
                "chunk_index": index,
                "text": current_text,
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"]
            })
            continue

        # Always take overlap from the original previous chunk.
        previous_text = str(chunks[index - 1]["text"])
        previous_words = previous_text.split()

        current_words = current_text.split()

        # Prevent the final chunk from exceeding MAX_CHUNK_WORDS.
        available_space = max(
            0,
            MAX_CHUNK_WORDS - len(current_words)
        )

        overlap_count = min(
            OVERLAP_WORDS,
            available_space
        )

        overlap = previous_words[-overlap_count:]

        if overlap:
            merged_text = (
                " ".join(overlap)
                + "\n\n"
                + current_text
            )

            # Overlap can include text from the previous chunk's pages.
            page_start = min(
                int(chunks[index - 1]["page_start"]),
                int(chunk["page_start"])
            )
        else:
            merged_text = current_text
            page_start = int(chunk["page_start"])

        result.append({
            "chunk_index": index,
            "text": merged_text,
            "page_start": page_start,
            "page_end": chunk["page_end"]
        })

    return result


def chunk_text(
    extracted_pages: list[dict[str, int | str]]
) -> list[dict[str, int | str]]:
    """Main page-aware chunking function."""

    if not extracted_pages:
        return []

    units = prepare_units(extracted_pages)

    chunks = build_chunks(units)

    chunks = add_overlap(chunks)

    return chunks
