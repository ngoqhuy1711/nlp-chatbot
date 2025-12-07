"""
Fallback Handler - Xử lý các câu hỏi không nhận diện được intent
"""  # Docstring mô tả module fallback

from typing import Any, Dict  # Type hints cho context và response

from services.processors import (  # Các hàm dữ liệu dùng để gợi ý fallback
    list_majors,  # Lấy danh sách ngành
    list_tuition,  # Lấy học phí
    list_scholarships,  # Lấy học bổng
    add_contact_suggestion,  # Chèn thông tin liên hệ vào message
)

DEFAULT_GUIDE = "Nếu bạn cần thêm thông tin khác, cứ nói với mình nhé."  # Câu hướng dẫn mặc định


def _message_with_contact(*parts: str) -> str:
    """Ghép thông điệp và chèn thông tin liên hệ."""  # Docstring helper
    content = "\n\n".join(
        p.strip() for p in parts if p and p.strip())  # Ghép các đoạn thông điệp và làm sạch khoảng trắng
    return add_contact_suggestion(content)  # Thêm gợi ý liên hệ cuối mỗi phản hồi fallback


def handle_fallback_query(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xử lý câu hỏi khi không nhận diện được intent rõ ràng

    Args:
        message: Câu hỏi từ người dùng
        context: Context hội thoại hiện tại

    Returns:
        Response fallback (tất cả đều có gợi ý liên hệ)
    """  # Docstring mô tả nhiệm vụ hàm
    message_lower = message.lower()  # Chuyển câu hỏi về chữ thường để dò từ khóa

    # Tìm kiếm từ khóa chung
    if any(word in message_lower for word in ["ngành", "môn", "học"]):  # Nếu người dùng nhắc tới ngành/môn/học
        results = list_majors()  # Lấy danh sách ngành cho người dùng chọn
        return {
            "type": "major_suggestions",  # Kiểu response là gợi ý ngành
            "data": results[:10],  # Top 10 ngành để tránh quá dài
            "message": _message_with_contact(
                "Mình gửi bạn danh sách một số ngành học nổi bật để tham khảo nhé.",  # Nội dung chính
                DEFAULT_GUIDE,  # Câu hướng dẫn
            ),
        }

    if any(word in message_lower for word in ["điểm", "chuẩn"]):  # Người dùng nhắc tới điểm
        return {
            "type": "score_help",  # Chỉ trả thông điệp hướng dẫn, không có data
            "message": _message_with_contact(
                'Bạn có thể hỏi về điểm chuẩn của từng ngành. '
                'Ví dụ: "Điểm chuẩn ngành Kiến trúc năm 2025" hoặc "Ngành CNTT lấy bao nhiêu điểm?"',
                # Gợi ý câu hỏi mẫu
                DEFAULT_GUIDE,
            ),
        }

    if any(word in message_lower for word in ["học phí", "tiền", "phí"]):  # Người dùng nhắc tới học phí
        results = list_tuition()  # Lấy bảng học phí
        return {
            "type": "tuition",  # Kiểu response: học phí
            "data": results,  # Đính kèm dữ liệu học phí
            "message": _message_with_contact(
                "Đây là thông tin học phí mà mình tìm được.",  # Nội dung chính
                DEFAULT_GUIDE,
            ),
        }

    if any(word in message_lower for word in ["học bổng", "scholarship"]):  # Người dùng nhắc tới học bổng
        results = list_scholarships()  # Lấy danh sách học bổng
        return {
            "type": "scholarships",  # Kiểu response
            "data": results,  # Dữ liệu học bổng
            "message": _message_with_contact(
                "Mình gửi bạn danh sách các học bổng hiện có của trường.",  # Nội dung chính
                DEFAULT_GUIDE,
            ),
        }

    # Không khớp từ khóa cụ thể -> trả hướng dẫn chung
    return {
        "type": "general_help",  # Kiểu response chung
        "message": _message_with_contact(
            "Mình có thể hỗ trợ bạn tra cứu các thông tin như điểm chuẩn, ngành học, học phí, học bổng hoặc chỉ tiêu tuyển sinh.",
            "Bạn đang cần biết điều gì để mình hỗ trợ nhanh nhất?",
        ),
    }
