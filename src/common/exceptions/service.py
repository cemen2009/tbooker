class ServiceError(Exception):
    """Base class for application service errors."""


class UserNotFoundError(ServiceError):
    """Raised when the requested user does not exist."""


class UserAlreadyExistsError(ServiceError):
    """Raised when a user with the requested unique data already exists."""
