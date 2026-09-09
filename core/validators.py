"""EduTrack Enterprise Input and Domain Validators."""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_phone_number(value: str) -> None:
    if not value:
        return
    pattern = re.compile(r'^\+?[0-9\s\-()]{7,20}$')
    if not pattern.match(value.strip()):
        raise ValidationError(_("Phone number must contain between 7 and 20 valid numeric digits or symbols."))

def validate_national_id(value: str) -> None:
    if not value:
        return
    clean_val = value.strip().replace('-', '').replace(' ', '')
    if len(clean_val) < 6 or len(clean_val) > 25:
        raise ValidationError(_("National ID or Passport number must be between 6 and 25 alphanumeric characters."))

def validate_gpa_range(value) -> None:
    if value is None:
        return
    try:
        val = float(value)
    except (ValueError, TypeError):
        raise ValidationError(_("GPA must be a valid decimal value."))
    if val < 0.0 or val > 5.0:
        raise ValidationError(_("GPA score must fall within the range 0.00 to 5.00."))

def validate_isbn_code(value: str) -> None:
    if not value:
        return
    clean = value.replace('-', '').replace(' ', '').upper()
    if len(clean) not in (10, 13):
        raise ValidationError(_("ISBN must contain exactly 10 or 13 digits."))

def validate_positive_amount(value) -> None:
    if value is not None and value < 0:
        raise ValidationError(_("Monetary amount must be strictly greater than or equal to zero."))
