import datetime
import streamlit as st
from app import post_api

st.title("Add Income/Expense Record")

record_type = st.radio("Record Type", ["Income", "Expense"], horizontal=True)
record_date = st.date_input("Record Date", value=datetime.date.today())
amount_input = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
remarks = st.text_input("Remark", placeholder="e.g., Bank interest / service fee")

col1, col2 = st.columns(2)

with col1:
    if st.button("CONFIRM", type="primary", use_container_width=True):
        if amount_input == 0:
            st.error("Amount cannot be 0.")
        else:
            signed_amount = amount_input if record_type == "Income" else -amount_input
            payload = {
                "amount": signed_amount,
                "record_date": record_date.isoformat(),
                "remarks": remarks or None,
            }
            response = post_api("ledger/record", payload)

            if response is None:
                st.error("Failed to connect to API server.")
            elif response.status_code == 200:
                st.success("Income/Expense record added successfully.")
            else:
                detail = response.json().get("detail", "Unknown error")
                st.error(f"Failed: {detail}")

with col2:
    if st.button("Reset", use_container_width=True):
        st.rerun()
