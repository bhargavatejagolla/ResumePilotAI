class ResumePilotException(Exception):
    """Base exception for ResumePilot AI."""
    pass


class ExtractionError(ResumePilotException):
    """Raised when PDF extraction fails."""
    pass


class LLMError(ResumePilotException):
    """Raised when LLM call fails or returns malformed response."""
    pass


class RenderingError(ResumePilotException):
    """Raised when HTML/PDF rendering fails."""
    pass
