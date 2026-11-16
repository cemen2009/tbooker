class RepositoryError(Exception):
    """Base class for persistence-layer errors."""


class DuplicateEntityError(RepositoryError):
    """Raised when an entity violates a uniqueness constraint."""
