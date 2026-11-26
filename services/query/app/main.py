
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.database import (
    connect_to_database,
    close_database_connection,
    get_pool,
)

from shared.exceptions import RAGException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    await connect_to_database()

    try:
        yield
    finally:
        # Application shutdown
        await close_database_connection()


app = FastAPI(
    title="RAG Query Service",
    description="Question answering and document retrieval API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RAGException)
async def rag_exception_handler(
    request: Request,
    exc: RAGException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/health")
async def health_check():
    pool = get_pool()

    result = await pool.fetchval("SELECT 1")

    return {
        "status": "healthy",
        "database": "connected" if result == 1 else "unavailable",
    }
