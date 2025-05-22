from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.exceptions import AppException
from app.models.schemas import ErrorResponse, ErrorDetail, ErrorCode
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def create_error_response(
    code: ErrorCode,
    message: str,
    status_code: int = 500,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """
    Crée une réponse d'erreur standardisée

    Args:
        code: Code d'erreur
        message: Message d'erreur
        status_code: Code de statut HTTP
        field: Champ concerné par l'erreur
        details: Détails supplémentaires de l'erreur
    """
    error_detail = ErrorDetail(
        code=code,
        message=message,
        field=field,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=error_detail).model_dump(),
    )


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware de gestion des erreurs

    Capture toutes les exceptions et les transforme en réponses JSON standardisées
    """
    try:
        return await call_next(request)
    except AppException as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return create_error_response(
            code=e.error_code,
            message=str(e.detail),
            status_code=e.status_code,
            field=getattr(e, "field", None),
            details=getattr(e, "details", None),
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return create_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(e),
            status_code=400,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        # En production, ne pas exposer les détails de l'erreur
        return create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="Une erreur interne s'est produite",
            status_code=500,
            details=(
                {"error": str(e)}
                if logger.getEffectiveLevel() <= logging.DEBUG
                else None
            ),
        )
