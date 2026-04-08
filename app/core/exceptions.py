from fastapi import HTTPException, status


class TutorRAGErrors(HTTPException):
    """Base exception class for TutorRAG system errors."""

    def __init__(
        self,
        detail: str = "An unexpected error occurred in the RAG system.",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)


class DocumentError(TutorRAGErrors):
    """Raised for document processing or access errors."""

    def __init__(
        self,
        detail: str = "Document operation failed.",
        status_code: int = status.HTTP_404_NOT_FOUND,
    ) -> None:
        super().__init__(detail=detail, status_code=status_code)


class RetrievalError(TutorRAGErrors):
    """Raised when retrieval fails."""

    def __init__(
        self,
        detail: str = "Retrieval process failed.",
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
    ) -> None:
        super().__init__(detail=detail, status_code=status_code)