import streamlit as st
from datetime import date
from ui_state import apply_mobile_layout, ensure_data_synced, get_api, init_session_state, post_api, refresh_all_data

init_session_state()
ensure_data_synced()
apply_mobile_layout()

st.title("Borrow / Repay Loan")

def update_input():
    st.session_state.borrow_amount = st.session_state.borrow_slider

def update_slider():
    max_val = float(st.session_state.get("borrow_max", 0.0) or 0.0)
    amount = float(st.session_state.get("borrow_amount", 0.0) or 0.0)
    if max_val:
        st.session_state.borrow_slider = min(amount, max_val)
    else:
        st.session_state.borrow_slider = amount

with st.expander("Borrow Loan", expanded=False):
    borrowers = get_api("borrowers") or []
    borrower_lookup = {b["name"]: b["id"] for b in borrowers}

    borrower_mode = st.radio(
        "Borrower",
        ["Existing Borrower", "First Time Borrower"],
        horizontal=True,
        key="borrow_mode",
    )

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

    borrow_date = st.date_input("Borrow date", value=date.today(), key="borrow_date")
    try:
        default_payback = date(borrow_date.year + 1, borrow_date.month, borrow_date.day)
    except ValueError:
        default_payback = date(borrow_date.year + 1, borrow_date.month, 28)

    plan_payback_date = st.date_input(
        "Expected payback date",
        value=default_payback,
        min_value=borrow_date,
        key="plan_payback_date",
    )

    max_available = 0.0
    if st.session_state.get("all_dash"):
        max_available = float(st.session_state["all_dash"].get("cash_on_hand", 0.0))

    st.session_state.borrow_max = max(100.0, max_available)
    default_amount = min(200.0, st.session_state.borrow_max)
    st.session_state.setdefault("borrow_slider", default_amount)
    st.session_state.setdefault("borrow_amount", default_amount)

    loan_amount = st.slider(
        "Loan amount",
        min_value=0.0,
        max_value=st.session_state.borrow_max,
        value=st.session_state.borrow_slider,
        step=100.0,
        key="borrow_slider",
        on_change=update_input
    )
    loan_amount = st.number_input(
        "Amount (RM)",
        min_value=0.0,
        value=st.session_state.borrow_amount,
        step=100.0,
        key="borrow_amount",
        on_change=update_slider,
    )

    st.caption(f"MAX Available RM {max_available:,.2f}")

    with st.container(border=True):
        st.markdown("**Interest Rate: 3% Per Annum**")
        selected_lending_date = st.session_state.get("borrow_date", borrow_date)
        selected_payback_date = st.session_state.get("plan_payback_date", plan_payback_date)
        quote = get_api(
            "loans/preview-quote",
            params={
                "principal": loan_amount,
                "lending_date": selected_lending_date.isoformat(),
                "plan_payback_date": selected_payback_date.isoformat(),
            },
        )
        if quote:
            st.write(f"Estimated interest is RM **{quote['interest']:,.2f}**")
            st.write(f"Total amount to pay back is RM **{quote['total']:,.2f}**")
        else:
            st.write("Estimated interest is RM **0.00**")
            st.write("Total amount to pay back is RM **0.00**")

    if st.button("Issue Loan", use_container_width=True, type="primary"):
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
            st.rerun()
        elif result:
            st.error(result.json().get("detail", "Loan issue failed"))
        else:
            st.error("Server connection error")


with st.expander("Repay Loan", expanded=False):
    active_loans = get_api("loans/active") or []

    if not active_loans:
        st.info("No active loans available for repayment.")
    else:
        loan_options = {
            (
                f"Loan #{loan['loan_id']} | {loan['borrower']} | "
                f"Principal RM {loan['principal']:,.2f} | "
                f"Last Payment Date {loan['lending_date']}"
            ): loan
            for loan in active_loans
        }

        selected_label = st.selectbox("Select active loan", options=list(loan_options.keys()))
        selected_loan = loan_options[selected_label]

        lending_date = selected_loan.get("lending_date", "-")
        with st.container(border=True):
            st.markdown("**Repayment Quote**")
            repay_date = st.date_input("Repayment date", value=date.today(), key="repay_date")
            interest_quote = get_api(
                "loans/interest-only",
                params={
                    "loan_id": int(selected_loan["loan_id"]),
                    "target_date": repay_date.isoformat(),
                },
            ) or {}
            interest_amount = float(interest_quote.get("interest", 0.0))
            principal_now = float(selected_loan.get("principal", 0.0))
            overall_outstanding = interest_amount + principal_now
            st.write(f"Interest from {lending_date} to {repay_date.isoformat()} is RM {interest_amount:,.2f}")
            st.write(f"Amount to fully settle is RM {overall_outstanding:,.2f}")

        repay_amount_seed = (int(selected_loan["loan_id"]), repay_date.isoformat())
        if st.session_state.get("repay_amount_seed") != repay_amount_seed:
            st.session_state.repay_amount = float(overall_outstanding)
            st.session_state.repay_amount_seed = repay_amount_seed

        st.markdown(
            """
            <style>
            div[data-testid="stForm"] button {
                background-color: #c0392b;
                color: #ffffff;
                border: 1px solid #c0392b;
            }
            div[data-testid="stForm"] button:hover {
                background-color: #a93226;
                border-color: #a93226;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.form("repay_form"):
            repayment_amount = st.number_input(
                "Repayment amount (RM)",
                min_value=0.0,
                value=st.session_state.get("repay_amount", float(overall_outstanding)),
                step=50.0,
                key="repay_amount",
            )
            submit_repayment = st.form_submit_button("Submit Repayment")

        if submit_repayment:
            if repayment_amount <= 0:
                st.error("Repayment amount must be greater than 0.")
            else:
                payload = {
                    "loan_id": int(selected_loan["loan_id"]),
                    "amount": float(repayment_amount),
                    "date_received": st.session_state.get("repay_date", date.today()).isoformat(),
                }
                res = post_api("loans/repay", payload)
                if res and res.status_code == 200:
                    data = res.json() if hasattr(res, "json") else {}
                    new_principal = float(data.get("new_principal", 0.0))
                    st.success(f"Repayment recorded. New principal: RM {new_principal:,.2f}")
                    st.session_state.is_synced = False
                    refresh_all_data()
                    st.rerun()
                elif res:
                    st.error(res.json().get("detail", "Repayment failed"))
                else:
                    st.error("Server connection error")

if st.button("Back to Dashboard", use_container_width=True):
    st.switch_page("dashboard.py")

if st.sidebar.button("Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
