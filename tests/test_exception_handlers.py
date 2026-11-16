import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from common.exceptions.api import register_exception_handlers
from common.exceptions.service import (
    ServiceError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (UserNotFoundError("User not found"), 404, "User not found"),
        (
            UserAlreadyExistsError("A user with this email already exists"),
            409,
            "A user with this email already exists",
        ),
        (ServiceError("Unexpected service failure"), 500, "Internal server error"),
    ],
)
def test_service_exceptions_are_translated_at_api_boundary(
    error, expected_status: int, expected_detail: str
) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def raise_service_error() -> None:
        raise error

    with TestClient(app) as client:
        response = client.get("/test")

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
