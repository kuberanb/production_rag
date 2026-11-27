

from openai import AsyncOpenAI

from shared.config import settings

client = AsyncOpenAI(
    api_key=settings.openai_api_key
)

async def generate_embedding(texts:list[str])-> list[list[float]]:
    """
    Generate embeddings for multiple text chunks.

    Returns embeddings in the same order as the input texts.
    """

    if not texts:
        return []

    if any(not text or not text.strip() for text in texts):
        raise ValueError(
            "Cannot generate embeddings for empty text"
        )

    all_embeddings = []

    batch_size = settings.embedding_batch_size

    for start in range(0,len(texts),batch_size):

        batch = texts[start:start + batch_size]

        response = await client.embeddings.create(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            input=batch
        )

        # Preserve the original input order.
        ordered_data = sorted(
            response.data,
            key=lambda item: item.index
        )

        if len(ordered_data) != len(batch):
            raise ValueError("Embedding response count does not match input count")

        for item in ordered_data:

            embedding = item.embedding

            if len(embedding) != settings.embedding_dimensions:
                raise ValueError(
                    f"Expected {settings.embedding_dimensions} dimensions, "
                    f"but received {len(embedding)}"
                )

            all_embeddings.append(embedding)

    return all_embeddings

