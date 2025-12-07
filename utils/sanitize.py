import html
import re
from typing import Optional


def sanitize_message(message: str, max_length: int = 1000) -> str:
    if not message:
        return ""

    message = message.strip()

    message = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', message)

    message = html.escape(message)

    message = re.sub(r'(.)\1{3,}', r'\1\1\1', message)

    message = re.sub(r'\s+', ' ', message)

    if len(message) > max_length:
        message = message[:max_length]

    dangerous_patterns = [
        r';\s*(DROP|DELETE|UPDATE|INSERT)\s+',
        r'(UNION|SELECT).*FROM',
        r'--\s*$',
        r'/\*.*\*/',
    ]
    for pattern in dangerous_patterns:
        message = re.sub(pattern, '', message, flags=re.IGNORECASE)

    return message.strip()


def validate_session_id(session_id: Optional[str]) -> str:
    if not session_id:
        return "default"

    session_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)

    if len(session_id) > 100:
        session_id = session_id[:100]

    return session_id if session_id else "default"


def remove_excessive_punctuation(text: str) -> str:
    text = re.sub(r'([!?.]){2,}', r'\1', text)
    return text


def detect_spam(message: str) -> bool:
    if not message:
        return False

    if len(message) > 20:
        uppercase_ratio = sum(1 for c in message if c.isupper()) / len(message)
        if uppercase_ratio > 0.8:
            return True

    url_count = len(re.findall(r'https?://', message))
    if url_count > 3:
        return True

    special_char_ratio = sum(1 for c in message if not c.isalnum() and not c.isspace()) / len(message)
    if special_char_ratio > 0.5:
        return True

    spam_patterns = [
        r'(click|clik)\s+(here|hear)',
        r'(buy|bye)\s+(now|naow)',
        r'(free|fr33)\s+(money|muney)',
        r'(win|winn)\s+\$\d+',
    ]
    for pattern in spam_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True

    return False


def normalize_vietnamese_text(text: str) -> str:
    text = text.replace('\u200b', '')
    text = text.replace('\ufeff', '')

    return text


__all__ = [
    'sanitize_message',
    'validate_session_id',
    'remove_excessive_punctuation',
    'detect_spam',
    'normalize_vietnamese_text',
]
