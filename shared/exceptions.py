
class RAGException(Exception):
    """Base exception for the RAG application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500
    ):
        self.message = message
        self.status_code = status_code

        super().__init__(message)


class DatabaseConnectionError(RAGException):
    """Raised when database connection fails."""

    def __init__(self, message="Database connection failed"):
        super().__init__(message, status_code=503)


class DocumentNotFoundError(RAGException):
    """Raised when a requested document does not exist."""

    def __init__(self, message="Document not found"):
        super().__init__(message, status_code=404)


class DocumentProcessingError(RAGException):
    """Raised when document processing fails."""

    def __init__(self, message="Document processing failed"):
        super().__init__(message, status_code=500)


class InvalidFileError(RAGException):
    """Raised when an uploaded file is invalid."""

    def __init__(self, message="Invalid file"):
        super().__init__(message, status_code=400)


class EmbeddingGenerationError(RAGException):
    """Raised when embedding generation fails."""

    def __init__(self, message="Embedding generation failed"):
        super().__init__(message, status_code=502)
