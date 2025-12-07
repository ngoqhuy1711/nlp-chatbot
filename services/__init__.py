"""
Services Package - Các dịch vụ xử lý nghiệp vụ cho backend

Package này chứa:
- nlp_service: Xử lý NLP và quản lý context hội thoại
- csv_service: Xử lý dữ liệu từ các file CSV
"""

from . import csv_service  # Re-export module csv_service để các nơi khác gọi trực tiếp
from .nlp_service import get_nlp_service, NLPService  # Expose singleton getter và class

__all__ = [
    "get_nlp_service",  # Cho phép import get_nlp_service từ services
    "NLPService",  # Cho phép truy cập class để test hoặc extend
    "csv_service",  # Cho phép import module csv_service
]
