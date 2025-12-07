"""API Exceptions - Lỗi liên quan API validation và processing."""  # Docstring mô tả module API exceptions

from typing import Optional, Dict, Any  # Type hints cho thuộc tính details/status

from . import ChatbotException  # Base class cho mọi exception tùy biến


class APIException(ChatbotException):
    """Base exception cho API errors."""  # Docstring mô tả lớp cơ sở API

    def __init__(
            self,
            message: str,
            error_code: str = "API_ERROR",
            status_code: int = 500,
            details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code  # Lưu HTTP status đi kèm lỗi
        super().__init__(message, error_code, details)  # Khởi tạo phần chung với ChatbotException

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()  # Bắt đầu từ dict cơ sở
        data["status_code"] = self.status_code  # Bổ sung status_code để logging/response
        return data  # Trả dict hoàn chỉnh


class ValidationError(APIException):
    """Lỗi validation request."""  # Docstring mô tả lỗi input

    def __init__(
            self,
            message: str = "Dữ liệu đầu vào không hợp lệ",
            field: Optional[str] = None,
            value: Optional[Any] = None,
            constraint: Optional[str] = None
    ):
        details = {  # Gom thông tin chi tiết vi phạm
            "field": field,
            "value": value,
            "constraint": constraint
        }
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",  # Mã lỗi chuẩn
            status_code=422,  # HTTP status cho lỗi validation
            details={k: v for k, v in details.items() if v is not None}  # Bỏ các trường None
        )


class RateLimitError(APIException):
    """Lỗi khi vượt quá rate limit."""  # Docstring mô tả lớp

    def __init__(
            self,
            message: str = "Quá nhiều yêu cầu, vui lòng thử lại sau",
            limit: Optional[int] = None,
            window: Optional[str] = None,
            retry_after: Optional[int] = None
    ):
        details = {  # Chi tiết giới hạn
            "limit": limit,
            "window": window,
            "retry_after": retry_after
        }
        super().__init__(
            message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,  # HTTP 429 Too Many Requests
            details={k: v for k, v in details.items() if v is not None}
        )


class AuthenticationError(APIException):
    """Lỗi xác thực."""  # Docstring mô tả lỗi auth

    def __init__(
            self,
            message: str = "Xác thực không thành công",
            provided_key: Optional[str] = None
    ):
        details = {"provided_key": provided_key} if provided_key else {}  # Chỉ thêm key khi có giá trị
        super().__init__(
            message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,  # HTTP Unauthorized
            details=details
        )


class ResourceNotFoundError(APIException):
    """Lỗi khi không tìm thấy resource."""  # Docstring mô tả lỗi 404

    def __init__(
            self,
            message: str = "Không tìm thấy tài nguyên",
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None
    ):
        details = {  # Tên và ID tài nguyên không tìm thấy
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(
            message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,  # HTTP Not Found
            details={k: v for k, v in details.items() if v is not None}
        )


__all__ = [  # Danh sách export của module
    "APIException",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "ResourceNotFoundError"
]
