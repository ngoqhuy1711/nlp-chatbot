from typing import Optional, Dict, Any

from . import ChatbotException


class APIException(ChatbotException):
    def __init__(
            self,
            message: str,
            error_code: str = "API_ERROR",
            status_code: int = 500,
            details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        super().__init__(message, error_code, details)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["status_code"] = self.status_code
        return data


class ValidationError(APIException):
    def __init__(
            self,
            message: str = "Dữ liệu đầu vào không hợp lệ",
            field: Optional[str] = None,
            value: Optional[Any] = None,
            constraint: Optional[str] = None
    ):
        details = {
            "field": field,
            "value": value,
            "constraint": constraint
        }
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={k: v for k, v in details.items() if v is not None}
        )


class RateLimitError(APIException):
    def __init__(
            self,
            message: str = "Quá nhiều yêu cầu, vui lòng thử lại sau",
            limit: Optional[int] = None,
            window: Optional[str] = None,
            retry_after: Optional[int] = None
    ):
        details = {
            "limit": limit,
            "window": window,
            "retry_after": retry_after
        }
        super().__init__(
            message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={k: v for k, v in details.items() if v is not None}
        )


class AuthenticationError(APIException):
    def __init__(
            self,
            message: str = "Xác thực không thành công",
            provided_key: Optional[str] = None
    ):
        details = {"provided_key": provided_key} if provided_key else {}
        super().__init__(
            message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class ResourceNotFoundError(APIException):
    def __init__(
            self,
            message: str = "Không tìm thấy tài nguyên",
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None
    ):
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(
            message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={k: v for k, v in details.items() if v is not None}
        )


__all__ = [
    "APIException",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "ResourceNotFoundError"
]
