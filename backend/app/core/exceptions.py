"""Custom exceptions for IlmuAI."""


class IlmuAIException(Exception):
    """Base exception for IlmuAI."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(IlmuAIException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(IlmuAIException):
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class AuthenticationError(IlmuAIException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class RateLimitError(IlmuAIException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class LLMError(IlmuAIException):
    """LLM API error."""

    def __init__(self, message: str = "LLM service error"):
        super().__init__(message, status_code=503)
