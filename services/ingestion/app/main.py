

from fastapi import FastAPI,Request
from contextlib import asynccontextmanager
from shared.database import (connect_to_database,close_database_connection,get_pool)
from shared.exceptions import RAGException
from fastapi.responses import JSONResponse
from services.ingestion.app.api.document import router as document_router

@asynccontextmanager
async def lifespan(app:FastAPI):
    # Application startup
    await connect_to_database()
    try:
        yield

    finally:
        # Application shutdown
        await close_database_connection()    


app = FastAPI(
    title="RAG Ingestion Service",
    description="Document ingestion and processing API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RAGException)
async def rag_exception_handler(request:Request,exc:RAGException,):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

app.include_router(document_router)


@app.get("/health")
async def health_check():
    pool = await get_pool()

    result = await pool.fetchval("SELECT 1")

    return {
        "status": "healthy",
        "database": "connected" if result == 1 else "unavailable",
    }



