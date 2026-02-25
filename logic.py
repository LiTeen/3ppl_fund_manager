import calendar
from decimal import ROUND_HALF_UP, Decimal
from datetime import date, datetime
from typing import Optional, Dict

from sqlmodel import Session, select, func
from models import (
    Member, Loan, Transaction_Ledger, Borrower, 
    Loan_Repayment, LoanStatus, TransactionCategory, PaymentType
)

# --- UTILITIES ---

def round_half_up(decimal_num: Decimal) -> Decimal:
    """Standard financial rounding to 2 decimal places."""
    return Decimal(str(decimal_num)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def days_in_year(year: int) -> int:
    """Handles leap years correctly for interest calculation."""
    return 365 + calendar.isleap(year)

# --- READ OPERATIONS ---

def get_loan_record(session: Session, loan_id: int) -> Optional[Loan]:
    """Fetches a loan from the database."""
    return session.get(Loan, loan_id)

def total_fund_value(session: Session) -> Decimal:
    """Sums all ledger entries and active loan principals."""
    # Sum Ledger
    ledger_sum = session.exec(select(func.sum(Transaction_Ledger.amount))).one() or Decimal(0)
    # Sum Active Loans (Not Closed)
    active_loan_sum = session.exec(
        select(func.sum(Loan.principal)).where(Loan.status != LoanStatus.CLOSED)
    ).one() or Decimal(0)
    
    return round_half_up(ledger_sum + active_loan_sum)

def check_total_stake(session: Session) -> bool:
    """Verifies that the sum of active member stakes equals exactly 1.00."""
    total_stake = session.exec(
        select(func.sum(Member.stake)).where(Member.is_active == True)
    ).one() or Decimal(0)
    
    # Using string comparison or threshold to avoid float precision issues
    return round_half_up(total_stake) == Decimal('1.00')

def get_member_shares(session: Session, member_id: int) -> Optional[Decimal]:
    """Calculates a specific member's share based on current fund valuation."""
    if not check_total_stake(session):
        print("Warning: Stake is not 100%.")
        return None
        
    member = session.get(Member, member_id)
    if not member:
        return None
        
    total_value = total_fund_value(session)
    share = total_value * member.stake
    return round_half_up(share)

# --- INTEREST & QUOTES ---

def calculate_interest(session: Session, loan_id: int, payment_date: date = None) -> Decimal:
    """Calculates 3% simple interest based on actual days elapsed."""
    loan = get_loan_record(session, loan_id)
    if not loan: return Decimal(0)

    target_date = payment_date or date.today()
    loan_days = (target_date - loan.lending_date).days
    
    interest = (loan.principal * loan.interest_rate * max(0, loan_days)) / days_in_year(loan.lending_date.year)
    return round_half_up(interest)

def calculate_required_payment(session: Session, loan_id: int, target_reduction: Decimal, target_date: date = None) -> Dict:
    """Tells the borrower how much total cash to pay to achieve a specific principal reduction."""
    interest_needed = calculate_interest(session, loan_id, target_date)
    total_required = target_reduction + interest_needed
    
    return { 
        'interest': interest_needed,
        'reduction': round_half_up(target_reduction),
        'total': round_half_up(total_required)
    }

# --- WRITE OPERATIONS (MUTATIONS) ---

def check_loan_status(session: Session, loan_id: int, date_receive_payment: date = None):
    """Updates loan status (Closed, Overdue, or Pending) based on balance and dates."""
    loan = get_loan_record(session, loan_id)
    if not loan: return

    if loan.principal <= 0:
        loan.status = LoanStatus.CLOSED
        loan.actual_payback_date = date_receive_payment or date.today()
    elif loan.plan_payback_date < date.today():
        loan.status = LoanStatus.OVERDUE
    else:
        loan.status = LoanStatus.PENDING
    
    session.add(loan)

def record_payment(session: Session, loan_id: int, amount_paid: Decimal, date_received: date):
    """Executes the waterfall payment: Interest first, then Principal."""
    loan = get_loan_record(session, loan_id)
    if not loan or amount_paid <= 0: return

    accrued_int = calculate_interest(session, loan_id, date_received)
    interest_portion = min(amount_paid, accrued_int)
    principal_reduction = round_half_up(amount_paid - interest_portion)

    # 1. Validation
    if loan.principal - principal_reduction < 0:
        print(f"Error: {principal_reduction} exceeds principal {loan.principal}")
        return

    # 2. Database Changes
    # Note: member_id=4 represents the 'General Fund' system account
    if interest_portion > 0:
        int_ledger = Transaction_Ledger(
            member_id=4, amount=interest_portion, 
            category=TransactionCategory.LOAN_INT_RECEIVED, loan_id=loan_id
        )
        session.add(int_ledger)

    if principal_reduction > 0:
        loan.principal = round_half_up(loan.principal - principal_reduction)
        pri_ledger = Transaction_Ledger(
            member_id=4, amount=principal_reduction, 
            category=TransactionCategory.PRINCIPAL_RETURNED, loan_id=loan_id
        )
        session.add(pri_ledger)

    # 3. Reset interest clock and extend plan date by 1 year (as requested)
    loan.lending_date = date_received
    if amount_paid > accrued_int:
        loan.plan_payback_date = date(date_received.year + 1, date_received.month, date_received.day)
    
    session.add(loan)

    # 4. Save Repayment Receipt
    payment_type = PaymentType.PRINCIPAL if principal_reduction > 0 else PaymentType.INTEREST
    repayment = Loan_Repayment(
        loan_id=loan.id, amount_paid=amount_paid, 
        date=date_received, payment_type=payment_type
    )
    session.add(repayment)

    # 5. Commit and Update Status
    session.commit()
    session.refresh(loan)
    check_loan_status(session, loan.id, date_received)
    session.commit()


def record_bank_interest(session: Session, amount: Decimal, interest_date: date, remarks: str = None):
    """Adds bank interest profit to the General Fund (Member 4)."""
    if amount <= 0:
        raise ValueError("Interest amount must be positive.")
    
    # Member 4 is your 'General Fund' system account
    new_entry = Transaction_Ledger(
        member_id=4, 
        amount=amount, 
        category=TransactionCategory.BANK_INT_RECEIVED,
        timestamp=datetime.combine(interest_date, datetime.min.time()),
        remarks=remarks or "FD Interest Received"
    )
    
    session.add(new_entry)
    session.commit()
    return new_entry


def record_member_withdrawal(session: Session, member_id: int, amount: Decimal, withdraw_date: date):
    # 1. Safety Check: Total Fund Cash vs. Withdrawal Amount
    total_val = total_fund_value(session)
    active_loans = session.exec(select(func.sum(Loan.principal)).where(Loan.status != LoanStatus.CLOSED)).one() or Decimal(0)
    cash_on_hand = total_val - active_loans

    if amount > cash_on_hand:
        raise ValueError(f"Insufficient cash. Max withdrawal allowed: RM {cash_on_hand}")

    # 2. Record the Ledger Entry (Negative Amount)
    withdrawal = Transaction_Ledger(
        member_id=member_id,
        amount=-amount,
        category=TransactionCategory.CAPITAL_WITHDRAW,
        timestamp=datetime.combine(withdraw_date, datetime.min.time()),
        remarks=f"Capital withdrawal by Member ID {member_id}"
    )
    session.add(withdrawal)
    session.commit()
    return withdrawal
