"""
Input Validators.

Comprehensive input validation and sanitization.
"""

import html
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Input validation utility class.

    Provides comprehensive validation for various input types.
    """

    # Email regex (RFC 5322 simplified)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Phone regex (Korean format)
    PHONE_REGEX = re.compile(
        r'^(\+82|0)\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}$'
    )

    # Password requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_REQUIREMENTS = {
        "uppercase": r'[A-Z]',
        "lowercase": r'[a-z]',
        "digit": r'\d',
        "special": r'[!@#$%^&*(),.?":{}|<>]',
    }

    # Dangerous characters for SQL/XSS
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', ';', '--', '/*', '*/']

    # URL schemes whitelist
    ALLOWED_URL_SCHEMES = ['http', 'https']

    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"

        if len(email) > 254:
            return False, "Email too long"

        email = email.strip().lower()

        if not cls.EMAIL_REGEX.match(email):
            return False, "Invalid email format"

        # Check for common typos
        common_domains = ['gmail.com', 'naver.com', 'daum.net', 'kakao.com']
        domain = email.split('@')[1]
        for cd in common_domains:
            if domain != cd and cls._levenshtein_distance(domain, cd) == 1:
                return False, f"Did you mean {cd}?"

        return True, None

    @classmethod
    def validate_password_strength(
        cls,
        password: str,
        require_all: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate
            require_all: Whether all requirements must be met

        Returns:
            Tuple of (is_valid, list of missing requirements)
        """
        if not password:
            return False, ["Password is required"]

        errors = []

        # Length check
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            errors.append(f"At least {cls.PASSWORD_MIN_LENGTH} characters")
        if len(password) > cls.PASSWORD_MAX_LENGTH:
            errors.append(f"Maximum {cls.PASSWORD_MAX_LENGTH} characters")

        # Complexity checks
        for req_name, pattern in cls.PASSWORD_REQUIREMENTS.items():
            if not re.search(pattern, password):
                errors.append(f"At least one {req_name} character")

        # Common password check
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123',
            'password123', 'admin123', 'letmein'
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common")

        if require_all:
            return len(errors) == 0, errors
        else:
            # Allow if at least 3 requirements met
            return len(errors) <= 2, errors

    @classmethod
    def validate_phone(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return True, None  # Phone is optional

        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)

        if not cls.PHONE_REGEX.match(phone):
            return False, "Invalid phone format (e.g., 010-1234-5678)"

        return True, None

    @classmethod
    def validate_url(
        cls,
        url: str,
        allowed_schemes: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format and scheme.

        Args:
            url: URL to validate
            allowed_schemes: List of allowed schemes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"

        schemes = allowed_schemes or cls.ALLOWED_URL_SCHEMES

        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                return False, "URL must include scheme (http/https)"

            if parsed.scheme not in schemes:
                return False, f"Scheme must be one of: {', '.join(schemes)}"

            if not parsed.netloc:
                return False, "Invalid URL format"

            return True, None

        except Exception:
            return False, "Invalid URL"

    @classmethod
    def validate_length(
        cls,
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
        field_name: str = "Value"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate string length.

        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            field_name: Name for error message

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            value = ""

        length = len(value)

        if length < min_length:
            return False, f"{field_name} must be at least {min_length} characters"

        if length > max_length:
            return False, f"{field_name} must be at most {max_length} characters"

        return True, None

    @classmethod
    def validate_name(cls, name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a person's name.

        Args:
            name: Name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Name is required"

        name = name.strip()

        if len(name) < 2:
            return False, "Name too short"

        if len(name) > 100:
            return False, "Name too long"

        # Check for invalid characters
        if re.search(r'[<>"\'\\/;]', name):
            return False, "Name contains invalid characters"

        return True, None

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return InputValidator._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


# =========================================================================
# Sanitization Functions
# =========================================================================

def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    Args:
        text: Text to sanitize
        allow_html: Whether to allow HTML tags

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # HTML escape if not allowed
    if not allow_html:
        text = html.escape(text)

    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize unicode
    import unicodedata
    text = unicodedata.normalize('NFKC', text)

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed"

    # Remove path components
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)

    # Limit length
    name, ext = (filename.rsplit('.', 1) + [''])[:2]
    if len(name) > 200:
        name = name[:200]
    if len(ext) > 10:
        ext = ext[:10]

    return f"{name}.{ext}" if ext else name


def sanitize_html(html_content: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML content, keeping only allowed tags.

    Args:
        html_content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags

    Returns:
        Sanitized HTML
    """
    if not html_content:
        return ""

    # Default allowed tags
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li']

    # Simple tag stripping (for production, use bleach library)
    import re

    # Remove script tags completely
    html_content = re.sub(
        r'<script[^>]*>.*?</script>',
        '',
        html_content,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove style tags
    html_content = re.sub(
        r'<style[^>]*>.*?</style>',
        '',
        html_content,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove event handlers
    html_content = re.sub(
        r'\s+on\w+\s*=\s*["\'][^"\']*["\']',
        '',
        html_content,
        flags=re.IGNORECASE
    )

    # Build allowed tags pattern
    tag_pattern = '|'.join(allowed_tags)

    # Remove disallowed tags but keep content
    html_content = re.sub(
        rf'<(?!/?)(?!({tag_pattern})\b)[^>]+>',
        '',
        html_content,
        flags=re.IGNORECASE
    )

    return html_content


# =========================================================================
# Convenience Functions
# =========================================================================

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address."""
    return InputValidator.validate_email(email)


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength."""
    return InputValidator.validate_password_strength(password)


def validate_and_sanitize(
    data: Dict[str, Any],
    schema: Dict[str, Dict]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and sanitize a dictionary of data.

    Args:
        data: Data to validate
        schema: Validation schema

    Schema format:
        {
            "field_name": {
                "type": "email" | "password" | "string" | "phone" | "url",
                "required": bool,
                "min_length": int,
                "max_length": int,
            }
        }

    Returns:
        Tuple of (sanitized_data, list of errors)
    """
    sanitized = {}
    errors = []

    for field, rules in schema.items():
        value = data.get(field)
        field_type = rules.get("type", "string")
        required = rules.get("required", False)

        # Check required
        if required and not value:
            errors.append(f"{field} is required")
            continue

        if not value:
            continue

        # Validate based on type
        if field_type == "email":
            is_valid, error = InputValidator.validate_email(value)
            if not is_valid:
                errors.append(f"{field}: {error}")
            else:
                sanitized[field] = value.strip().lower()

        elif field_type == "password":
            is_valid, password_errors = InputValidator.validate_password_strength(value)
            if not is_valid:
                errors.extend([f"{field}: {e}" for e in password_errors])
            else:
                sanitized[field] = value

        elif field_type == "phone":
            is_valid, error = InputValidator.validate_phone(value)
            if not is_valid:
                errors.append(f"{field}: {error}")
            else:
                sanitized[field] = value

        elif field_type == "url":
            is_valid, error = InputValidator.validate_url(value)
            if not is_valid:
                errors.append(f"{field}: {error}")
            else:
                sanitized[field] = value

        else:  # string
            min_len = rules.get("min_length", 0)
            max_len = rules.get("max_length", 10000)
            is_valid, error = InputValidator.validate_length(
                value, min_len, max_len, field
            )
            if not is_valid:
                errors.append(error)
            else:
                sanitized[field] = sanitize_input(value)

    return sanitized, errors
