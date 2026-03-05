from fastapi import FastAPI, HTTPException, Depends, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict
from database import engine, create_db_and_tables, get_session
import logic 
from models import (
    Member, Loan, LoanStatus, Borrower, 
    Transaction_Ledger, TransactionCategory, SQLModel
)
import test_logic 

app = FastAPI(title="Fund Manager API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your phone to connect
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure tables are created on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Pydantic Models for Input ---
# This ensures all your Pydantic models handle Decimals correctly
class BaseSchema(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=False, json_encoders={Decimal: float})

class RepaymentRequest(BaseSchema):
    loan_id: int
    amount: Decimal
    date_received: date

class LoanCreate(BaseSchema):
    borrower_id: int
    principal: Decimal
    lending_date: date = date.today()
    plan_payback_date: date = date(lending_date.year + 1,lending_date.month,lending_date.day)
    

class BorrowerCreate(BaseSchema):
    name: str

class BankInterestRequest(BaseSchema):
    amount: Decimal
    record_interest_date: date
    remarks: Optional[str] = "FD Interest Received"

class ExpensesRequest(BaseSchema):
    amount: Decimal
    record_expense_date: date
    remarks: Optional[str] = "Expense out"


class WithdrawalRequest(BaseSchema): # Uses the Decimal-safe base
    member_id: int
    amount: Decimal
    date: date

class GlobalWithdrawRequest(BaseSchema):
    total_amount: Decimal
    withdraw_date: date
  


# --- Routes ---
# @app.get("/borrowers/search")
# def search_borrower(name: str, session: Session = Depends(get_session)):
#     statement = select(Borrower).where(Borrower.name.contains(name))
#     results = session.exec(statement).all()
#     return results # Returns a list of borrowers with their IDs

@app.get("/")
def root():
    return {"status": "Online", "fund": "Active"}

@app.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    """The main overview for Teen, Jacky, and WCH."""
    total_val = logic.total_fund_value(session)
    
    active_loans = session.exec(select(Loan).where(Loan.status != LoanStatus.CLOSED)).all()
    total_lent = sum(loan.principal for loan in active_loans)
    
    total_profit, _ = logic.calculate_total_profit(session)
   
    members = session.exec(select(Member).where(Member.id < 4)).all()
    member_data = []
    for m in members:
        share_val = logic.get_member_shares(session, m.id)
        member_data.append({
            "name": m.name,
            "stake_pct": float(m.stake * 100),
            "current_value": float(share_val) if share_val else 0.0
        })

    return {
        "total_valuation": float(total_val),
        "cash_on_hand": float(total_val - total_lent),
        "total_lent": float(total_lent),
        "profit_earned": float(total_profit),
        "members": member_data
    }

@app.get("/members", response_model=List[Member])
def get_all_members(session: Session = Depends(get_session)):
    return session.exec(select(Member)).all()

@app.post("/members/withdraw")
def member_withdraw(data: WithdrawalRequest, session: Session = Depends(get_session)):
    try:
        entry = logic.record_member_withdrawal(session, data.member_id, data.amount, data.date)
        return {"status": "Success", "amount": float(entry.amount)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
#@app.post("/members/withdraw-global")
def withdraw_global(data: GlobalWithdrawRequest, session: Session = Depends(get_session)):
    """Triggers a withdrawal for all partners based on their stakes."""
    try:
        result = logic.record_global_withdrawal(session, data.total_amount, data.withdraw_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Show All Loan
@app.get("/loans")
def get_all_loans(session: Session = Depends(get_session)):
    statement = select(Loan).order_by(Loan.status.desc())
    loans = session.exec(statement).all()
    
    results = []
    for loan in loans:
        results.append({
            "id": loan.id,
            "loan_id": loan.id,
            "borrower": loan.borrower.name,
            "principal": float(loan.principal),
            "interest_rate": float(loan.interest_rate),
            "lending_date": loan.lending_date.isoformat(),
            "plan_payback_date": loan.plan_payback_date.isoformat(),
            "actual_payback_date": loan.actual_payback_date.isoformat() if loan.actual_payback_date else None,
            "status": loan.status.value
        })
    return results


@app.get("/loans/active")
def list_active_loans(session: Session = Depends(get_session)):
    """Shows all people who currently owe money + live interest."""
    statement = select(Loan).where(Loan.status != LoanStatus.CLOSED)
    loans = session.exec(statement).all()
    
    results = []
    for loan in loans:
        results.append({
            "loan_id": loan.id,
            "borrower": loan.borrower.name, # Relationship magic
            "principal": float(loan.principal),
            "accrued_interest": float(logic.calculate_interest(loan)),
            "due_date": loan.plan_payback_date,
            "status": loan.status
        })
    return results

"""Duplicates of loan/quote"""
@app.get("/loans/calculator")
def get_total_needed(loan_id: int, target_reduction: Decimal, target_date: date, session: Session = Depends(get_session)):
   
    loan = logic.get_loan_record(session, loan_id)
    if not loan: return {"total": 0}
    interest = logic.calculate_interest(loan, target_date)
    return {"total": float(target_reduction + interest)}

# Create New Loan
@app.post("/loans/issue")
def create_loan(data: LoanCreate, session: Session = Depends(get_session)):
    """Issue a new loan and automatically record the cash leaving the fund."""
    # Safety Check: Do we have enough cash?
    current_cash = logic.get_loanable_balance(session)
    if float(data.principal) > current_cash:
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Max available: {current_cash}")
    
    # Fetch the borrower to get the name
    borrower = session.get(Borrower, data.borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    
    # check borrow amount must be more than 0
    if data.principal > 0:
        # Create the Loan
        new_loan = Loan(
            borrower_id=data.borrower_id,
            principal=data.principal,
            lending_date=data.lending_date,
            plan_payback_date=data.plan_payback_date,
            status=LoanStatus.PENDING
        )
        session.add(new_loan)
        session.flush() # Get the loan ID before committing

        # Create the Ledger Entry (Money leaving the fund)
        # Member 4 = General Fund / System Account
        ledger_entry = Transaction_Ledger(
            member_id=4,
            amount=-data.principal, # Negative because cash is leaving
            category=TransactionCategory.LOAN_OUT,
            loan_id=new_loan.id,
            remarks=f"Loan issued to {borrower.name}"
        )
        session.add(ledger_entry)
        
        session.commit()
        return {"message": "Loan issued successfully", "loan_id": new_loan.id}
    else:
        return {"message": "Loan amount cannot be 0 or negative."}

@app.get("/loans/quote")
def get_repayment_quote(
    loan_id: int, 
    target_reduction: Decimal, 
    target_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """How much to pay to reduce principal by X? (Includes interest)."""
    quote = logic.calculate_required_payment(session, loan_id, target_reduction, target_date)
    # Convert Decimals to floats for JSON
    return {k: float(v) for k, v in quote.items()}

@app.post("/loans/repay")
def record_repayment(data: RepaymentRequest, session: Session = Depends(get_session)):
    """The 'Submit' button when you receive cash."""
    try:
        # Call the logic function
        updated_loan = logic.record_payment(
            session, 
            loan_id=data.loan_id, 
            amount_paid=data.amount, 
            date_received=data.date_received
        )
        
        # updated_loan is guaranteed to exist here because 
        # logic.py raises an exception if it doesn't.
        return {
            "message": "Repayment Successful", 
            "new_principal": float(updated_loan.principal),
            "status": updated_loan.status
        }

    except ValueError as ve:
        # This catches "Loan not found" or "Overpayment"
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        # This catches unexpected system/db errors
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


# Show All Ledger
@app.get("/ledger")
def get_full_ledger(session: Session = Depends(get_session)):
    """A full audit trail of every cent that entered or left the fund."""
    statement = select(Transaction_Ledger).order_by(Transaction_Ledger.timestamp.desc())
    entries = session.exec(statement).all()
    
    results = []
    for entry in entries:
        results.append({
            "id": entry.id,
            "member_id": entry.member_id,
            "member_name": entry.member.name if entry.member else "Unknown",
            "amount": float(entry.amount),
            "timestamp": entry.timestamp.isoformat(),
            "loan_id": entry.loan_id,
            "category": entry.category.value,
            "remarks": entry.remarks
        })
    return results

@app.post("/ledger/expense")    
def record_expense(data: ExpensesRequest, session: Session = Depends(get_session)):
    """Records expenses by the fund's bank account (Member 4)."""
    try:
        new_expense = logic.record_expense_interest(
            session=session,
            amount= data.amount,
            interest_date=data.record_expense_date,
            remarks=data.remarks
        )

        return {
            "status": "success",
            "message": f"Recorded {new_expense.amount} expense to General Fund",
            "transaction_id": new_expense.id
        }
    except ValueError as ve:
        raise HTTPException(status_code=400,detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/ledger/income")    
def record_income(data: BankInterestRequest, session: Session = Depends(get_session)):
    """Records interest earned by the fund's bank account (Member 4)."""
    try:
        new_income = logic.record_expense_interest(
            session=session,
            amount= data.amount,
            interest_date=data.record_interest_date,
            remarks=data.remarks
        )

        return {
            "status": "success",
            "message": f"Recorded {new_income.amount} income to General Fund",
            "transaction_id": new_income.id
        }
    except ValueError as ve:
        raise HTTPException(status_code=400,detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/ledger/filter")


@app.get("/loans/interest-only")
def get_interest_only(loan_id: int, target_date: date, session: Session = Depends(get_session)):
    loan = logic.get_loan_record(session, loan_id)
    if not loan: return {"interest": 0}
    interest = logic.calculate_interest(loan, target_date)
    return {"interest": float(interest)}

# Show Only Profit Earned
@app.get("/profit")
def get_profit_report(session: Session = Depends(get_session)):
    total_profit, breakdown = logic.calculate_total_profit(session)
    return {
        "total_profit_earned": float(total_profit),
        "breakdown": breakdown
    }

# Create new borrower
@app.post("/borrowers", response_model=Borrower)
def create_borrower(data: BorrowerCreate, session: Session = Depends(get_session)):
    """Add a new person to the system so you can lend to them."""
    new_borrower = Borrower(name=data.name)
    session.add(new_borrower)
    try:
        session.commit()
        session.refresh(new_borrower)
        return new_borrower
    except Exception:
        session.rollback()
        raise HTTPException(status_code=400, detail="Borrower already exists")



@app.post("/loans/refresh-all")
def refresh_all_loan_statuses(session: Session = Depends(get_session)):
    """Checks every active loan and marks as 'od' if past plan_payback_date."""
    active_loans = session.exec(select(Loan).where(Loan.status != LoanStatus.CLOSED)).all()
    updated_count = 0
    
    for loan in active_loans:
        if loan.plan_payback_date < date.today():
            loan.status = LoanStatus.OVERDUE
            session.add(loan)
            updated_count += 1
            
    session.commit()
    return {"message": f"Refresh complete. {updated_count} loans updated to Overdue."}




#--- TEST Routes ---
# @app.post("/test")
# def test_in_main(session: Session = Depends(get_session)):
#     test_logic.test(session)