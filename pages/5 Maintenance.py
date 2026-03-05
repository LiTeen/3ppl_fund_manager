import streamlit as st
from app import init_session_state, delete_api, refresh_all_data

init_session_state()
refresh_all_data()

st.title("Maintenance")

st.subheader("Delete Loan Record")
all_loans = st.session_state.get("all_loans", [])
loan_options = {
    f"Loan #{loan['id']} | {loan['borrower']} | RM {loan['principal']:,.2f} | {loan['status']}": loan["id"]
    for loan in all_loans
}

if loan_options:
    selected_loan_label = st.selectbox("Choose loan to delete", list(loan_options.keys()))
    selected_loan_id = loan_options[selected_loan_label]

    if st.button("Delete Selected Loan", type="primary"):
        res = delete_api(f"maintenance/loans/{selected_loan_id}")
        if res and res.status_code == 200:
            st.success(res.json().get("message", "Loan deleted."))
            st.session_state.is_synced = False
            refresh_all_data()
            st.rerun()
        elif res:
            st.error(res.json().get("detail", "Failed to delete loan."))
        else:
            st.error("Server connection error.")
else:
    st.info("No loan records found.")

st.divider()
st.subheader("Delete Ledger Transaction")
all_ledger = st.session_state.get("all_ledger", [])
ledger_options = {
    f"Txn #{entry['id']} | {entry['category']} | RM {entry['amount']:,.2f} | {entry['timestamp']}": entry["id"]
    for entry in all_ledger
}

if ledger_options:
    selected_ledger_label = st.selectbox("Choose ledger transaction to delete", list(ledger_options.keys()))
    selected_ledger_id = ledger_options[selected_ledger_label]

    if st.button("Delete Selected Ledger Entry"):
        res = delete_api(f"maintenance/ledger/{selected_ledger_id}")
        if res and res.status_code == 200:
            st.success(res.json().get("message", "Ledger entry deleted."))
            st.session_state.is_synced = False
            refresh_all_data()
            st.rerun()
        elif res:
            st.error(res.json().get("detail", "Failed to delete ledger entry."))
        else:
            st.error("Server connection error.")
else:
    st.info("No ledger records found.")

if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
