from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# --- Enums for Choices ---

class LoanStatus(str, Enum):
    PENDING = "pd"
    OVERDUE = "od"
    CLOSED = "cl"

class TransactionCategory(str, Enum):
    CAPITAL_WITHDRAW = "capital_withdraw"
    BANK_INT_RECEIVED = "bank_int_received"
    LOAN_OUT = "loan_out"
    PRINCIPAL_RETURNED = "principal_returned"
    LOAN_INT_RECEIVED = "loan_int_received"
    CAPITAL_IN = "capital_in"
    EXPENSE_OUT = "expense_out"

class PaymentType(str, Enum):
    INTEREST = "i"
    PRINCIPAL = "p"

# --- Tables ---

class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    initial_capital: Decimal = Field(max_digits=12, decimal_places=2)
    join_date: date
    stake: Decimal = Field(max_digits=3, decimal_places=2)
    is_active: bool = Field(default=True)
    
    transactions: List["Transaction_Ledger"] = Relationship(back_populates="member")

class Borrower(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    
    loans: List["Loan"] = Relationship(back_populates="borrower")

class Loan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    borrower_id: int = Field(foreign_key="borrower.id")
    principal: Decimal = Field(max_digits=12, decimal_places=2)
    interest_rate: Decimal = Field(default=0.03, max_digits=3, decimal_places=2)
    lending_date: date
    plan_payback_date: date
    actual_payback_date: Optional[date] = Field(default=None)
    status: LoanStatus = Field(default=LoanStatus.PENDING)

    borrower: Borrower = Relationship(back_populates="loans")
    repayments: List["Loan_Repayment"] = Relationship(back_populates="loan")

class Transaction_Ledger(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="member.id")
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    timestamp: datetime = Field(default_factory=datetime.now)
    loan_id: Optional[int] = Field(default=None, foreign_key="loan.id")
    category: TransactionCategory
    remarks: Optional[str] = Field(default=None, max_length=300)

    member: Member = Relationship(back_populates="transactions")

class Loan_Repayment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loan_id: int = Field(foreign_key="loan.id")
    amount_paid: Decimal = Field(max_digits=12, decimal_places=2)
    date: date
    payment_type: PaymentType
    remarks: Optional[str] = Field(default=None, max_length=300)

    loan: Loan = Relationship(back_populates="repayments")
