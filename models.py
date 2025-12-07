"""Models - Pydantic models cho request/response validation."""  # Docstring mô tả module models

from datetime import datetime, timezone  # Dùng timestamp UTC cho response
from typing import Optional, List, Dict, Any  # Type hints cho field Pydantic

from pydantic import BaseModel, Field, field_validator  # Công cụ định nghĩa schema và validator


# Error Response Models
class ErrorDetail(BaseModel):
    field: Optional[str] = None  # Tên trường gây lỗi (nếu có)
    value: Optional[Any] = None  # Giá trị người dùng gửi lên
    constraint: Optional[str] = None  # Ràng buộc vi phạm
    suggestion: Optional[str] = None  # Gợi ý sửa lỗi


class ErrorResponse(BaseModel):
    success: bool = False  # Luôn false vì đây là lỗi
    error_code: str  # Mã lỗi chuẩn hóa
    error_message: str  # Thông điệp lỗi hiển thị cho người dùng
    details: Dict[str, Any] = Field(default_factory=dict)  # Chi tiết bổ sung (nếu có)
    request_id: Optional[str] = None  # Request ID để trace log
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())  # Dấu thời gian UTC


class ValidationErrorResponse(ErrorResponse):
    error_code: str = "VALIDATION_ERROR"  # Override mã lỗi mặc định
    validation_errors: List[ErrorDetail] = Field(default_factory=list)  # Danh sách lỗi theo từng field


# Request Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)  # Tin nhắn bắt buộc, tối thiểu 1 ký tự

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():  # Loại bỏ trường hợp toàn khoảng trắng
            raise ValueError("Câu hỏi không được để trống")  # Ném lỗi validation
        return v.strip()  # Trả về chuỗi đã strip


class AdvancedChatRequest(BaseModel):
    message: str = Field(..., min_length=1)  # Tin nhắn bắt buộc
    session_id: Optional[str] = "default"  # Session ID, default "default"
    use_context: Optional[bool] = True  # Cho phép bật/tắt context theo request

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():  # Loại bỏ input rỗng
            raise ValueError("Câu hỏi không được để trống")
        return v.strip()


class ContextRequest(BaseModel):
    action: str  # Hành động cần thực hiện (get/set/reset)
    session_id: Optional[str] = "default"  # Session cần thao tác
    context: Optional[Dict[str, Any]] = None  # Payload context khi set

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        from constants import Validation  # Import tại runtime tránh vòng lặp
        if v not in Validation.VALID_ACTIONS:  # Kiểm tra action hợp lệ
            raise ValueError(f"Action không hợp lệ. Chỉ chấp nhận: {', '.join(Validation.VALID_ACTIONS)}")
        return v


class SuggestMajorsRequest(BaseModel):
    score: float = Field(..., ge=0, le=30)  # Điểm đầu vào, giới hạn 0-30
    score_type: Optional[str] = "chuan"  # Loại điểm (chuẩn/sàn)
    year: Optional[str] = "2025"  # Năm mục tiêu

    @field_validator("score_type")
    @classmethod
    def validate_score_type(cls, v: str) -> str:
        from constants import Validation  # Import động để tránh vòng lặp
        if v not in Validation.VALID_SCORE_TYPES:  # Chỉ chấp nhận chuan/san
            raise ValueError(f"Loại điểm không hợp lệ. Chỉ chấp nhận: {', '.join(Validation.VALID_SCORE_TYPES)}")
        return v


# Response Models
class BaseResponse(BaseModel):
    success: bool = True  # Mặc định thành công
    message: Optional[str] = None  # Thông điệp kèm theo


class DataResponse(BaseResponse):
    data: List[Dict[str, Any]] = Field(default_factory=list)  # Payload dữ liệu dạng list
    count: int = 0  # Tổng số bản ghi

    def __init__(self, **data):
        super().__init__(**data)  # Gọi BaseModel init
        if "count" not in data and "data" in data:  # Nếu caller không truyền count
            self.count = len(data["data"])  # Tự động set count theo độ dài data


class NLPAnalysisResponse(BaseResponse):
    intent: str  # Intent dự đoán
    confidence: float = Field(..., ge=0, le=1)  # Score [0,1]
    entities: List[Dict[str, Any]] = Field(default_factory=list)  # Entity trích xuất


class ChatResponse(BaseResponse):
    analysis: Dict[str, Any]  # Tóm tắt intent/entity/score
    response: Dict[str, Any]  # Payload phản hồi cho UI
    context: Optional[Dict[str, Any]] = None  # Context cập nhật


class ContextResponse(BaseResponse):
    context: Dict[str, Any] = Field(default_factory=dict)  # Context hiện tại của session


# Utility Functions
def create_success_response(data: Optional[List[Dict[str, Any]]] = None, message: Optional[str] = None) -> Dict[
    str, Any]:
    if data is not None:  # Nếu có mảng dữ liệu
        return DataResponse(success=True, message=message, data=data,
                            count=len(data)).model_dump()  # Serialise DataResponse
    return BaseResponse(success=True, message=message).model_dump()  # Ngược lại chỉ trả message


def create_error_response(message: str, error_code: Optional[str] = None, error_detail: Optional[str] = None) -> Dict[
    str, Any]:
    return ErrorResponse(success=False, error_message=message, error_code=error_code,
                         details={
                             "error_detail": error_detail} if error_detail else {}).model_dump()  # Chuẩn hóa error payload


def create_nlp_response(intent: str, confidence: float, entities: List[Dict[str, Any]],
                        message: Optional[str] = None) -> Dict[str, Any]:
    return NLPAnalysisResponse(success=True, message=message, intent=intent, confidence=confidence,
                               entities=entities).model_dump()  # Helper trả analysis chuẩn
