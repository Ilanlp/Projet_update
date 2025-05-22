from fastapi import HTTPException
from typing import Optional, Dict, Any
from app.models.schemas import ErrorCode


class AppException(HTTPException):
    """Exception de base pour l'application"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.error_code = error_code
        self.field = field
        self.details = details
        super().__init__(status_code=status_code, detail=message)


class NotFoundException(AppException):
    """Exception pour les ressources non trouvées"""

    def __init__(
        self,
        message: str = "Resource not found",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=404,
            field=field,
            details=details,
        )


class ValidationException(AppException):
    """Exception pour les erreurs de validation"""

    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=400,
            field=field,
            details=details,
        )


class DatabaseException(AppException):
    """Exception pour les erreurs de base de données"""

    def __init__(
        self,
        message: str = "Database error",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=500,
            field=field,
            details=details,
        )
