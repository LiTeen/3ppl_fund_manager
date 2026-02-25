from sqlmodel import SQLModel, create_engine, Session
from models import Member, Borrower, Loan, Transaction_Ledger, Loan_Repayment # Import to register tables

sqlite_file_name = "fund.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False is required for SQLite + FastAPI
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    """Run this once to create the fund.db file and tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for FastAPI routes to get a database session."""
    with Session(engine) as session:
        yield session
