from decimal import ROUND_HALF_UP, Decimal
from datetime import date, datetime
from typing import Optional, Dict
from sqlmodel import Session, select, func
from util import round_half_up,calculate_interest
from models import (
    Member, Loan, Transaction_Ledger, 
    Loan_Repayment, LoanStatus, TransactionCategory, PaymentType
)

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

def get_loanable_balance(session: Session) -> Decimal:
    """
    Calculates how much cash is actually available to be lent out.
    Formula: Sum of all Ledger entries (Inflow - Outflow)
    """
    # Summing the 'amount' column in the Transaction_Ledger
    total_balance = session.query(func.sum(Transaction_Ledger.amount)).scalar() or 0
    
    return Decimal(total_balance or 0)

# --- WRITE OPERATIONS (MUTATIONS) ---
def calculate_total_profit(session: Session):
    """Business logic to sum all interest received."""
    categories = [TransactionCategory.BANK_INT_RECEIVED, TransactionCategory.LOAN_INT_RECEIVED]
    
    # Sum total
    profit_statement = select(func.sum(Transaction_Ledger.amount)).where(Transaction_Ledger.category.in_(categories))
    total_profit = session.exec(profit_statement).one() or Decimal(0)
    
    # Get breakdown
    breakdown = {}
    for cat in categories:
        val = session.exec(select(func.sum(Transaction_Ledger.amount)).where(Transaction_Ledger.category == cat)).one() or Decimal(0)
        breakdown[cat.value] = float(val)
        
    return total_profit, breakdown

def calculate_required_payment(session: Session, loan_id: int, target_reduction: Decimal, target_date: date = None) -> Dict:
    """Tells the borrower how much total cash to pay to achieve a specific principal reduction."""
    loan_instance = session.get(Loan, loan_id)
    
    if not loan_instance:
        raise ValueError(f"Loan with ID {loan_id} not found.")

    interest_needed = calculate_interest(loan_instance, target_date)
    
    total_required = target_reduction + interest_needed
    
    return { 
        'interest': interest_needed,
        'reduction': round_half_up(target_reduction),
        'total': round_half_up(total_required)
    }



def preview_new_loan_quote(principal: Decimal, lending_date: date, plan_payback_date: date) -> Dict:
    """Returns projected interest and total repayment for a brand new loan."""
    if principal <= 0:
        raise ValueError("Principal must be greater than 0.")

    if plan_payback_date < lending_date:
        raise ValueError("Plan payback date cannot be earlier than lending date.")

    preview_loan = Loan(
        borrower_id=0,
        principal=principal,
        interest_rate=Decimal('0.03'),
        lending_date=lending_date,
        plan_payback_date=plan_payback_date,
        status=LoanStatus.PENDING,
    )

    interest_needed = calculate_interest(preview_loan, plan_payback_date)
    total_required = round_half_up(principal + interest_needed)

    return {
        'interest': interest_needed,
        'principal': round_half_up(principal),
        'total': total_required,
    }

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
    
    # 1. DATABASE LOOKUP (Requires Session)
    loan = get_loan_record(session, loan_id)
    if not loan:
        raise ValueError(f"Loan ID {loan_id} not found.")

    if amount_paid <= 0:
        raise ValueError("Repayment amount must be greater than zero.")

    # 2. CALCULATION (Pass the loan object, NO session needed here anymore)
    accrued_int = calculate_interest(loan, date_received)
    
    interest_portion = min(amount_paid, accrued_int)
    principal_reduction = round_half_up(amount_paid - interest_portion)

    # 3. VALIDATION
    if loan.principal - principal_reduction < 0:
        raise ValueError(f"Payment exceeds principal. Max allowed principal reduction: {loan.principal}")

    # 4. DATABASE CHANGES (Uses the session provided)
    borrower_name = loan.borrower.name if loan.borrower else "Unknown borrower"
    payment_remark = f"Paid by {borrower_name}"
    if date_received < date.today():
        get_timestamp = datetime.combine(date_received, datetime.min.time())
    else:
        get_timestamp = datetime.now()

    if interest_portion > 0:
        int_ledger = Transaction_Ledger(
            member_id=4, 
            amount=interest_portion, 
            category=TransactionCategory.LOAN_INT_RECEIVED, 
            loan_id=loan.id,
            timestamp=get_timestamp,
            remarks=payment_remark,
        )
        session.add(int_ledger)

    if principal_reduction > 0:
        loan.principal = round_half_up(loan.principal - principal_reduction)
        pri_ledger = Transaction_Ledger(
            member_id=4, 
            amount=principal_reduction, 
            category=TransactionCategory.PRINCIPAL_RETURNED, 
            loan_id=loan.id,
            timestamp=get_timestamp,
            remarks=payment_remark,
        )
        session.add(pri_ledger)

    # 5. UPDATE LOAN STATE
    loan.lending_date = date_received
    if amount_paid > accrued_int:
        # Simple +1 year logic
        try:
            loan.plan_payback_date = date(date_received.year + 1, date_received.month, date_received.day)
        except ValueError: 
            # Handles Feb 29th edge case: move to Feb 28th next year
            loan.plan_payback_date = date(date_received.year + 1, 2, 28)
    
    # 6. SAVE REPAYMENT RECEIPT
    payment_type = PaymentType.PRINCIPAL if principal_reduction > 0 else PaymentType.INTEREST
    repayment = Loan_Repayment(
        loan_id=loan.id, 
        amount_paid=amount_paid, 
        date=date_received, 
        payment_type=payment_type
    )
    session.add(repayment)

    # 7. FINALIZE (Atomic commit)
    session.commit()
    session.refresh(loan)
    
    # Only use session for functions that internally hit the DB
    check_loan_status(session, loan.id, date_received)
    
    session.commit()
    session.refresh(loan) 
    
    return loan


def record_income_expense(session: Session, amount: Decimal, record_date: date, remarks: str = None):
    """Adds either income or expense entry to the General Fund (Member 4)."""
    if amount == 0:
        raise ValueError("Amount cannot be 0.")

    cleaned_remarks = remarks.strip() if isinstance(remarks, str) else None

    if amount > 0:
        new_entry = Transaction_Ledger(
            member_id=4,
            amount=amount,
            category=TransactionCategory.BANK_INT_RECEIVED,
            timestamp=datetime.combine(record_date, datetime.min.time()),
            remarks=cleaned_remarks or "Income record"
        )
    else:
        new_entry = Transaction_Ledger(
            member_id=4,
            amount=amount,
            category=TransactionCategory.EXPENSE_OUT,
            timestamp=datetime.combine(record_date, datetime.min.time()),
            remarks=cleaned_remarks or "Expense record"
        )

    session.add(new_entry)
    session.commit()
    return new_entry


def record_member_withdrawal(session: Session, member_id: int, amount: Decimal, withdraw_date: date):
    # 1. Fetch the Member object
    member = session.get(Member, member_id)
    if not member:
        raise ValueError("Member not found")

    # 2. Safety Check: Fund Cash vs. Withdrawal Amount
    total_val = total_fund_value(session)
    active_loans = session.exec(
        select(func.sum(Loan.principal)).where(Loan.status != LoanStatus.CLOSED)
    ).one() or Decimal(0)
    cash_on_hand = total_val - active_loans

    if amount > cash_on_hand:
        raise ValueError(f"Insufficient cash. Max allowed: RM {cash_on_hand}")

    # 3. Safety Check: Member's own capital
    # We shouldn't let them withdraw more than they technically own
    if amount > member.initial_capital:
        raise ValueError(f"Withdrawal exceeds your initial capital (RM {member.initial_capital})")

    # 4. Record the Ledger Entry (The "Audit Trail")
    withdrawal_entry = Transaction_Ledger(
        member_id=member_id,
        amount=-amount,
        category=TransactionCategory.CAPITAL_WITHDRAW,
        timestamp=datetime.combine(withdraw_date, datetime.min.time()),
        remarks=f"Capital withdrawal by {member.name}"
    )
    
    # 5. Update the Member Model (The "New Principal")
    member.initial_capital -= amount

    # 6. Commit both changes at once
    session.add(withdrawal_entry)
    session.add(member)
    session.commit()
    
    session.refresh(member)
    return withdrawal_entry


def record_global_withdrawal(session: Session, total_amount: Decimal, withdraw_date: date):
    """Withdraws a total sum and splits it across all active members based on their stakes."""
    
    # 1. Safety Check: Fund Cash vs. Total Withdrawal
    total_val = total_fund_value(session)
    active_loans = session.exec(
        select(func.sum(Loan.principal)).where(Loan.status != LoanStatus.CLOSED)
    ).one() or Decimal(0)
    cash_on_hand = total_val - active_loans

    if total_amount > cash_on_hand:
        raise ValueError(f"Insufficient cash. Max allowed: RM {cash_on_hand}")

    # 2. Fetch all active members
    members = session.exec(select(Member).where(Member.is_active == True)).all()
    
    with session.begin_nested(): # Create a sub-transaction
        for member in members:
            # Calculate this member's portion
            member_portion = round_half_up(total_amount * member.stake)
            
            # A. Record the Ledger Entry (Audit Trail)
            withdrawal_entry = Transaction_Ledger(
                member_id=member.id,
                amount=-member_portion,
                category=TransactionCategory.CAPITAL_WITHDRAW,
                timestamp=datetime.combine(withdraw_date, datetime.min.time()),
                remarks=f"Global withdrawal split for {member.name} (Total: RM {total_amount})"
            )
            session.add(withdrawal_entry)
            
            # B. Reduce the Member's Initial Capital
            member.initial_capital -= member_portion
            session.add(member)

    session.commit()
    return {"total_withdrawn": float(total_amount), "status": "Success"}
