from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Dict
from datetime import date, datetime
from sqlmodel import Session
import calendar
from models import Loan


# --- FUNCTION ---

def round_half_up(decimal_num: Decimal) -> Decimal:
    """Standard financial rounding to 2 decimal places."""
    return Decimal(str(decimal_num)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def days_in_year(year: int) -> int:
    """Handles leap years correctly for interest calculation."""
    return 365 + calendar.isleap(year)

# --- INTEREST & QUOTES ---
def calculate_interest(loan: Loan, payment_date: date = None) -> Decimal:

    """Calculates 3% simple interest based on actual days elapsed."""
    # No need to check 'if not loan' here because we pass it in
    target_date = payment_date or date.today()
    loan_days = (target_date - loan.lending_date).days
    
    # Use the loan object properties directly
    interest = (loan.principal * loan.interest_rate * max(0, loan_days)) / days_in_year(loan.lending_date.year)
    return round_half_up(interest)

