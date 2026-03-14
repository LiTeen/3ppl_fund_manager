import streamlit as st
from datetime import date
from ui_state import apply_mobile_layout, ensure_data_synced, init_session_state, post_api, refresh_all_data

init_session_state()
ensure_data_synced()
apply_mobile_layout()

st.title("Record Income/Expense")

entry_type = st.radio("Entry Type", ["Interest Income", "Expense"], horizontal=True)
record_date = st.date_input("Record Date", value=date.today())
amount_input = st.number_input("Amount (RM)", min_value=0.0, value=0.0, step=10.0)
remarks = st.text_input("Remarks (optional)")

if st.button("Submit", type="primary", use_container_width=True):
    if amount_input <= 0:
        st.error("Amount must be greater than 0.")
    else:
        signed_amount = amount_input if entry_type == "Interest Income" else -amount_input
        payload = {
            "amount": signed_amount,
            "record_date": record_date.isoformat(),
            "remarks": remarks.strip() or None,
        }
        res = post_api("ledger/record", payload)
        if res and res.status_code == 200:
            st.success("Entry recorded.")
            st.session_state.is_synced = False
            refresh_all_data()
            st.switch_page("dashboard.py")
        elif res:
            st.error(res.json().get("detail", "Failed to record entry."))
        else:
            st.error("Server connection error.")

if st.button("Back to Dashboard", use_container_width=True):
    st.switch_page("dashboard.py")

if st.sidebar.button("Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
