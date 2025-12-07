"""NLP Service - Xử lý ngôn ngữ tự nhiên và quản lý context hội thoại."""  # Docstring mô tả module

from typing import Dict, Any  # Type hints cho context và payload

from config import get_intent_threshold, get_context_history_limit  # Hàm đọc cấu hình cho intent/context
from nlu.pipeline import NLPPipeline  # Pipeline NLP lõi xử lý intent/entity


class ContextStore:
    """Lưu trữ context hội thoại trong RAM. Production nên dùng Redis."""  # Docstring mô tả store

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}  # Dictionary lưu context theo session_id

    def get(self, session_id: str) -> Dict[str, Any]:
        """Lấy context của session."""  # Docstring mô tả getter
        return self._store.get(session_id, {})  # Trả context nếu có, mặc định {}

    def set(self, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Đặt context cho session."""  # Docstring setter
        self._store[session_id] = context  # Lưu context mới vào store
        return context  # Trả context để chain

    def reset(self, session_id: str) -> None:
        """Xóa context của session."""  # Docstring reset
        if session_id in self._store:  # Chỉ xóa khi tồn tại
            del self._store[session_id]  # Xóa context khỏi store

    def append_history(self, session_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm entry vào lịch sử hội thoại (giới hạn 10 câu)."""  # Docstring append
        ctx = self.get(session_id)  # Lấy context hiện tại
        hist = ctx.get("conversation_history", []) + [entry]  # Thêm entry mới vào lịch sử

        limit = get_context_history_limit()  # Đọc giới hạn từ config
        if len(hist) > limit:  # Nếu lịch sử vượt giới hạn
            hist = hist[-limit:]  # Cắt bớt giữ các entry cuối

        ctx["conversation_history"] = hist  # Ghi lịch sử mới vào context
        self.set(session_id, ctx)  # Lưu context cập nhật
        return ctx  # Trả context để upstream dùng


class NLPService:
    """Service NLP tổng hợp - Điều phối xử lý ngôn ngữ, context và dữ liệu."""  # Docstring mô tả service

    def __init__(self) -> None:
        """Khởi tạo NLP Service (chỉ gọi 1 lần khi app khởi động)."""  # Docstring init
        self.pipeline = NLPPipeline()  # Tạo instance pipeline NLP
        self.context_store = ContextStore()  # Khởi tạo store context trong RAM
        self.intent_threshold = get_intent_threshold()  # Lưu ngưỡng intent từ config

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """Phân tích NLP đơn giản - Chỉ trả intent + entities."""  # Docstring
        return self.pipeline.analyze(message)  # Delegate việc phân tích cho pipeline

    def handle_message(self, message: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý câu hỏi hoàn chỉnh: NLP + lấy dữ liệu + fallback.

        Flow: Analyze NLP → Check confidence → Get data hoặc Fallback
        """  # Docstring mô tả flow
        from services import csv_service as csvs  # Import lazy để tránh circular

        analysis = self.pipeline.analyze(message)  # Phân tích intent/entity

        if analysis["intent"] == "fallback" or analysis["score"] < self.intent_threshold:  # Kiểm tra score/intent
            response = csvs.handle_fallback_query(message, current_context)  # Gọi fallback handler
            analysis["intent"] = "fallback_response"  # Đổi intent để UI biết đây là fallback
        else:
            response = csvs.handle_intent_query(analysis, current_context, message)  # Điều hướng đến intent handler

        return {"analysis": analysis, "response": response}  # Trả cả phân tích lẫn phản hồi

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Lấy context của session."""  # Docstring
        return self.context_store.get(session_id)  # Delegate cho store

    def set_context(self, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Lưu context cho session."""  # Docstring
        return self.context_store.set(session_id, context)  # Delegate cho store

    def reset_context(self, session_id: str) -> None:
        """Xóa context (bắt đầu hội thoại mới)."""  # Docstring
        self.context_store.reset(session_id)  # Delegate cho store

    def append_history(self, session_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm entry vào lịch sử hội thoại."""  # Docstring
        return self.context_store.append_history(session_id, entry)  # Delegate cho store


# Singleton instance
nlp_service = NLPService()  # Tạo instance duy nhất khi module load


def get_nlp_service() -> NLPService:
    """Trả về singleton instance của NLPService."""  # Docstring
    return nlp_service  # Trả instance toàn cục
