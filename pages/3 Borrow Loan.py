import streamlit as st
from datetime import date
from ui_state import ensure_data_synced, get_api, init_session_state, post_api, refresh_all_data

init_session_state()
ensure_data_synced()

st.title("Loan")

borrowers = get_api("borrowers") or []
borrower_lookup = {b["name"]: b["id"] for b in borrowers}

borrower_mode = st.radio("Borrower", ["Existing Borrower", "First Time Borrower"], horizontal=True)

selected_borrower_id = None
borrower_name = None
if borrower_mode == "Existing Borrower":
    if borrower_lookup:
        selected_name = st.selectbox("Borrower Name", options=list(borrower_lookup.keys()))
        selected_borrower_id = borrower_lookup[selected_name]
    else:
        st.warning("No borrowers found. Switch to 'First Time Borrower'.")
else:
    borrower_name = st.text_input("Borrower Name")

borrow_date = st.date_input("Borrow date", value=date.today())
try:
    default_payback = date(borrow_date.year + 1, borrow_date.month, borrow_date.day)
except ValueError:
    default_payback = date(borrow_date.year + 1, borrow_date.month, 28)
plan_payback_date = st.date_input("Expect payback date", value=default_payback, min_value=borrow_date)

max_available = 0.0
if st.session_state.get("all_dash"):
    max_available = float(st.session_state["all_dash"].get("cash_on_hand", 0.0))

loan_amount = st.slider(
    "Loan amount",
    min_value=0.0,
    max_value=max(100.0, max_available),
    value=min(200.0, max(100.0, max_available)),
    step=100.0,
)
loan_amount = st.number_input("Amount (RM)", min_value=0.0, value=loan_amount, step=100.0)

st.caption(f"MAX Available RM {max_available:,.2f}")

with st.container(border=True):
    st.markdown("**Interest Rate: 3% Per Annum**")
    quote = get_api(
        "loans/preview-quote",
        params={
            "principal": loan_amount,
            "lending_date": borrow_date.isoformat(),
            "plan_payback_date": plan_payback_date.isoformat(),
        },
    )
    if quote:
        st.write(f"Estimated interest is RM **{quote['interest']:,.2f}**")
        st.write(f"Total amount need to pay back is RM **{quote['total']:,.2f}**")
    else:
        st.write("Estimated interest is RM **0.00**")
        st.write("Total amount need to pay back is RM **0.00**")

col1, col2 = st.columns(2)

with col1:
    if st.button("CONFIRM", use_container_width=True, type="primary"):
        if loan_amount <= 0:
            st.error("Loan amount must be greater than 0.")
            st.stop()

        if borrower_mode == "First Time Borrower":
            if not borrower_name or not borrower_name.strip():
                st.error("Borrower name is required.")
                st.stop()

        payload = {
            "borrower_id": selected_borrower_id,
            "borrower_name": borrower_name.strip() if borrower_name else None,
            "principal": loan_amount,
            "lending_date": borrow_date.isoformat(),
            "plan_payback_date": plan_payback_date.isoformat(),
        }
        result = post_api("loans/issue", payload)
        if result and result.status_code == 200:
            st.success("Loan issued successfully")
            st.session_state.is_synced = False
            refresh_all_data()
            st.switch_page("pages/1 Dashboard.py")
        elif result:
            st.error(result.json().get("detail", "Loan issue failed"))
        else:
            st.error("Server connection error")

with col2:
    if st.button("CANCEL", use_container_width=True):
        st.switch_page("pages/1 Dashboard.py")

if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
