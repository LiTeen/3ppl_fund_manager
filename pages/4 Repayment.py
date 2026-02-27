import streamlit as st
import requests
from datetime import date
from app import post_api, get_api
from app import refresh_all_data

st.header("💸 Record Loan Repayment")

# Access data from session state synced in app.py
repay_data = st.session_state.all_loans

# Filter for ACTIVE loans to populate the dropdown
active_loans = {
    f"{l['borrower']} - RM {l['principal']:,.2f}": l['id'] 
    for l in repay_data if l['status'] == 'pd'
}

if not active_loans:
    st.warning("No active loans found.")
    st.stop()

# --- Main Repayment Form ---
selected_loan_label = st.selectbox("Choose Loan:", options=list(active_loans.keys()))
loan_id = active_loans[selected_loan_label]

amount = st.number_input("Amount:", min_value=0.0, step=100.0)
repay_date = st.date_input("Date:", value=date.today())

st.markdown("<span style='color:red; font-weight:bold;'>Note: Interest will be paid first.</span>", unsafe_allow_html=True)

# Waterfall logic: Tell the user the total cost to reduce principal by 'amount'
if amount > 0:
    try:
        # Note: Using get_api for the calculation quote
        calc_resp = get_api("loans/calculate-total", params={
            "loan_id": loan_id,
            "target_reduction": amount,
            "target_date": repay_date.isoformat()
        })
        
        if calc_resp and 'total' in calc_resp:
            st.info(f"To fully pay principal {{ **RM {amount:,.2f}** }} today, the total is {{ **RM {calc_resp['total']:,.2f}** }}")
    except Exception:
        st.warning("Could not calculate total at this time.")

# --- Interest Calculator Box (Design as per image) ---
st.markdown("---")
with st.container(border=True):
    st.subheader("Interest calculator")
    calc_date = st.date_input("Target Payback Date:", value=repay_date, key="calc_date_box")
    calc_amount = st.number_input("Amount:", value=amount, key="calc_amount_box")
    
    if st.button("Calculate", key="calc_btn"):
        params = {"loan_id": loan_id, "target_date": calc_date.isoformat()}
        interest_val = get_api("loans/interest-only", params=params)
        
        if interest_val and 'interest' in interest_val:
            st.write(f"Interest is **RM {interest_val['interest']:,.2f}**")

st.markdown("<br>", unsafe_allow_html=True)

# --- Action Buttons ---
# Using columns to simulate 'stretch' width
col1, col2 = st.columns(2)

with col1:
    if st.button("CONFIRM", type="primary", use_container_width=True):
        payload = {
            "loan_id": loan_id, 
            "amount": amount, 
            "date_received": repay_date.isoformat()
        }
        res = post_api("loans/repay", data=payload)
        
        if res and res.status_code == 200:
            st.success("Repayment Confirmed!")
            # Reset sync so app.py refreshes data on next run
            st.session_state.is_synced = False 
            refresh_all_data()
            st.rerun()
            
        elif res:
            st.error(res.json().get('detail', "Repayment failed."))
        else:
            st.error("Server connection error.")

with col2:
    if st.button("CANCEL", use_container_width=True):
        st.rerun()

    # Provide a Refresh Button
if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()