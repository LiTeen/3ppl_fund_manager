import streamlit as st
import pandas as pd

# Query the local SQLite DB directly using SQLModel
from sqlmodel import select
from database import engine, create_db_and_tables
from seed import seed_initial_data
from models import Loan, Borrower, LoanStatus


st.title('Loan List')

res_loans = request