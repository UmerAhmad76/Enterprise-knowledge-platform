"""Domain-level exceptions. Services raise these; API layer maps them to HTTP codes."""


class EKPError(Exception):
    """Base class for all platform errors."""


class NotFoundError(EKPError):
    """Requested resource does not exist OR the caller is not allowed to see it."""


class AccessDeniedError(EKPError):
    """Caller is authenticated but lacks permission for the operation."""