"""Mathematical Precision and Edge-Case Calculation Routines."""
from decimal import Decimal, ROUND_HALF_UP

def round_grade_points(value: Decimal) -> Decimal:
    """Rounds grade points to standard institutional hundredths."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def compute_penalty_interest(principal: Decimal, annual_rate: Decimal, overdue_days: int, grace_days: int = 7) -> Decimal:
    """Calculates late fee penalties incorporating institutional grace periods."""
    chargeable_days = max(0, overdue_days - grace_days)
    if chargeable_days == 0:
        return Decimal("0.00")
    daily_rate = annual_rate / Decimal("365.0")
    return (principal * daily_rate * Decimal(chargeable_days)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
