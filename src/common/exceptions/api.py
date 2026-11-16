import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from common.exceptions.service import (
    ServiceError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)

_SERVICE_ERROR_STATUS_CODES = {
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
}


async def service_exception_handler(
    request: Request, error: Exception
) -> JSONResponse:
    status_code = next(
        (
            error_status
            for error_type, error_status in _SERVICE_ERROR_STATUS_CODES.items()
            if isinstance(error, error_type)
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            "Unhandled service exception for %s %s: %s",
            request.method,
            request.url.path,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )
        detail = "Internal server error"
    else:
        detail = str(error)

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, service_exception_handler)
