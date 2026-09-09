"""EduTrack Enterprise Global Utility Routines."""

import hashlib
import uuid
from decimal import Decimal
from django.utils import timezone

def generate_unique_code(prefix: str = "EDUTRACK", length: int = 8) -> str:
    token = uuid.uuid4().hex[:length].upper()
    return f"{prefix}-{token}"

def compute_sha256_checksum(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def format_currency_amount(amount: Decimal) -> str:
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

def calculate_percentage(part: int, whole: int) -> float:
    if not whole or whole == 0:
        return 0.0
    return round((float(part) / float(whole)) * 100.0, 2)
