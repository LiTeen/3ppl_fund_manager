import streamlit as st
from ui_state import delete_api, ensure_data_synced, init_session_state, refresh_all_data

init_session_state()
ensure_data_synced()

st.title("Maintenance")

all_loans = st.session_state.get("all_loans", [])

st.subheader("Loan List")
loan_view = st.radio(
    "Filter loans",
    ["Active Loan", "Closed Loan", "All Loan"],
    horizontal=True,
)

if loan_view == "Active Loan":
    filtered_loans = [loan for loan in all_loans if loan.get("status") in ("pd", "od")]
elif loan_view == "Closed Loan":
    filtered_loans = [loan for loan in all_loans if loan.get("status") == "cl"]
else:
    filtered_loans = all_loans

status_label = {
    "pd": "Pending",
    "od": "Overdue",
    "cl": "Closed",
}

if filtered_loans:
    st.caption(f"Showing {len(filtered_loans)} loan(s)")
    for loan in filtered_loans:
        col1, col2, col3, col4 = st.columns([0.7, 1.6, 1, 1.2])
        with col1:
            st.write(f"#{loan['id']}")
        with col2:
            st.write(loan["borrower"])
        with col3:
            st.write(f"RM {loan['principal']:,.2f}")
        with col4:
            st.write(status_label.get(loan.get("status"), loan.get("status", "-")))
else:
    st.info("No loans found for this filter.")

st.divider()
st.subheader("Delete Loan Record")

loan_options = {
    f"Loan #{loan['id']} | {loan['borrower']} | RM {loan['principal']:,.2f} | {status_label.get(loan.get('status'), loan.get('status', '-'))}": loan["id"]
    for loan in filtered_loans
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
    st.info("No deletable loan records for this filter.")

if st.sidebar.button("Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
