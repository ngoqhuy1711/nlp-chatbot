from typing import Optional, Dict, Any


class ChatbotException(Exception):
    def __repr__(self) -> str:
        return f"{self.error_code}: {self.message}"

    def __str__(self) -> str:
        if self.details:
            return f"{self.error_code}: {self.message} (Details: {self.details})"
        return f"{self.error_code}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "details": self.details,
        }

    def __init__(
            self,
            message: str,
            error_code: str = "CHATBOT_ERROR",
            details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.details = details or {}
        self.error_code = error_code
        self.message = message


from .nlp_exceptions import (  # noqa: E402
    NLPException,
    IntentNotFoundError,
    EntityExtractionError,
    ContextError,
    PreprocessingError,
)
from .data_exceptions import (  # noqa: E402
    DataException,
    DataNotFoundError,
    CSVLoadError,
    InvalidMajorError,
    DataValidationError,
)
from .api_exceptions import (  # noqa: E402
    APIException,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    ResourceNotFoundError,
)

__all__ = [
    "ChatbotException",
    "NLPException",
    "IntentNotFoundError",
    "EntityExtractionError",
    "ContextError",
    "PreprocessingError",
    "DataException",
    "DataNotFoundError",
    "CSVLoadError",
    "InvalidMajorError",
    "DataValidationError",
    "APIException",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "ResourceNotFoundError",
]
