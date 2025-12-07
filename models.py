from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    value: Optional[Any] = None
    constraint: Optional[str] = None
    suggestion: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    error_message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ValidationErrorResponse(ErrorResponse):
    error_code: str = "VALIDATION_ERROR"
    validation_errors: List[ErrorDetail] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Câu hỏi không được để trống")
        return v.strip()


class AdvancedChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = "default"
    use_context: Optional[bool] = True

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Câu hỏi không được để trống")
        return v.strip()


class ContextRequest(BaseModel):
    action: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        from constants import Validation
        if v not in Validation.VALID_ACTIONS:
            raise ValueError(f"Action không hợp lệ. Chỉ chấp nhận: {', '.join(Validation.VALID_ACTIONS)}")
        return v


class SuggestMajorsRequest(BaseModel):
    score: float = Field(..., ge=0, le=30)
    score_type: Optional[str] = "chuan"
    year: Optional[str] = "2025"

    @field_validator("score_type")
    @classmethod
    def validate_score_type(cls, v: str) -> str:
        from constants import Validation
        if v not in Validation.VALID_SCORE_TYPES:
            raise ValueError(f"Loại điểm không hợp lệ. Chỉ chấp nhận: {', '.join(Validation.VALID_SCORE_TYPES)}")
        return v


class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class DataResponse(BaseResponse):
    data: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if "count" not in data and "data" in data:
            self.count = len(data["data"])


class NLPAnalysisResponse(BaseResponse):
    intent: str
    confidence: float = Field(..., ge=0, le=1)
    entities: List[Dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseResponse):
    analysis: Dict[str, Any]
    response: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class ContextResponse(BaseResponse):
    context: Dict[str, Any] = Field(default_factory=dict)


def create_success_response(data: Optional[List[Dict[str, Any]]] = None, message: Optional[str] = None) -> Dict[
    str, Any]:
    if data is not None:
        return DataResponse(success=True, message=message, data=data,
                            count=len(data)).model_dump()
    return BaseResponse(success=True, message=message).model_dump()


def create_error_response(message: str, error_code: Optional[str] = None, error_detail: Optional[str] = None) -> Dict[
    str, Any]:
    return ErrorResponse(success=False, error_message=message, error_code=error_code,
                         details={
                             "error_detail": error_detail} if error_detail else {}).model_dump()


def create_nlp_response(intent: str, confidence: float, entities: List[Dict[str, Any]],
                        message: Optional[str] = None) -> Dict[str, Any]:
    return NLPAnalysisResponse(success=True, message=message, intent=intent, confidence=confidence,
                               entities=entities).model_dump()
