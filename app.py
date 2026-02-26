import streamlit as st
import requests
import pandas as pd
from datetime import date

# --- CONFIGURATION ---
# Use 'localhost' for laptop testing, or your Laptop IP (e.g. 192.168.1.XX) for mobile
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Main", layout="wide", page_icon="💰")

# --- API HELPERS ---
def get_api(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", params=params)
        return res.json() if res.status_code == 200 else None

    except: return None

def post_api(endpoint, data):
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=data)
        return res
    except: return None

# --- MAIN UI ---
st.title("🏦 3PPL Private Fund")

# # Navigation Tabs
# tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💸 Loans", "📜 Ledger", "⚙️ Admin"])

# # --- TAB 1: DASHBOARD ---
# with tab1:
#     data = get_api("dashboard")
#     if data:
#         sum_data = data["summary"]
#         c1, c2, c3 = st.columns(3)
#         c1.metric("Total Fund Value", f"RM {sum_data['total_valuation']:,.2f}")
#         c2.metric("Cash on Hand", f"RM {sum_data['cash_on_hand']:,.2f}")
#         c3.metric("Active Loans", f"RM {sum_data['total_lent']:,.2f}")
        
#         st.subheader("Partner Equity")
#         m_cols = st.columns(3)
#         for i, m in enumerate(data["members"]):
#             with m_cols[i]:
#                 st.info(f"**{m['name']}**\n\n**RM {m['current_value']:,.2f}**\n\nStake: {m['stake']}")
        
#         # Profit Section
#         profit_data = get_api("profit")
#         if profit_data:
#             st.success(f"📈 Total Profit Earned to Date: **RM {profit_data['total_profit_earned']:,.2f}**")

# # --- TAB 2: LOANS ---
# with tab2:
#     col_l, col_r = st.columns([2, 1])
    
#     with col_l:
#         st.subheader("Active Loans")
#         loans = get_api("loans/active")
#         if loans:
#             df_loans = pd.DataFrame(loans)
#             st.dataframe(df_loans, use_container_width=True, hide_index=True)
#         else:
#             st.write("No active loans.")

#     with col_r:
#         st.subheader("Repayment Tool")
#         with st.expander("Record a Payment", expanded=True):
#             l_id = st.number_input("Loan ID", min_value=1, step=1)
#             amt = st.number_input("Amount Paid (RM)", min_value=0.0)
#             d_rec = st.date_input("Date Received", value=date.today())
            
#             # Waterfall Quote Feature
#             if l_id and amt > 0:
#                 quote = get_api("loans/quote", params={"loan_id": l_id, "target_reduction": 0})
#                 if quote:
#                     st.caption(f"Accrued Interest Owed: RM {quote['interest']:.2f}")

#             if st.button("Confirm Repayment"):
#                 payload = {"loan_id": l_id, "amount": amt, "date_received": str(d_rec)}
#                 res = post_api("loans/repay", payload)
#                 if res and res.status_code == 200:
#                     st.success("Payment Recorded!")
#                     st.rerun()
#                 else:
#                     st.error("Failed to record. Check Loan ID or Amount.")

# # --- TAB 3: LEDGER ---
# with tab3:
#     st.subheader("Full Transaction History")
#     ledger = get_api("ledger/")
#     if ledger:
#         df_ledger = pd.DataFrame(ledger)
#         # Clean up columns for display
#         display_df = df_ledger[['timestamp', 'category', 'amount', 'remarks']]
#         st.table(display_df.head(20)) # Show latest 20

# # --- TAB 4: ADMIN ---
# with tab4:
#     st.subheader("New Operations")
    
#     # 1. Search/Add Borrower
#     c_b1, c_b2 = st.columns(2)
#     with c_b1:
#         st.write("**Add New Borrower**")
#         b_name = st.text_input("Borrower Name")
#         if st.button("Register Borrower"):
#             res = post_api("borrowers/", {"name": b_name})
#             if res and res.status_code == 200: st.success(f"Registered {b_name}!")
    
#     with c_b2:
#         st.write("**Find Borrower ID**")
#         search_q = st.text_input("Search Name")
#         if search_q:
#             results = get_api("borrowers/search", params={"name": search_q})
#             if results: st.write(results)

#     st.divider()
    
#     # 2. Issue New Loan
#     st.write("**Issue New Loan**")
#     c_ln1, c_ln2, c_ln3 = st.columns(3)
#     b_id = c_ln1.number_input("Borrower ID", min_value=1)
#     ln_amt = c_ln2.number_input("Principal Amount", min_value=0.0)
#     ln_date = c_ln3.date_input("Lending Date", value=date.today())
#     ln_payback = st.date_input("Plan Payback Date")
    
#     if st.button("Create Loan Contract"):
#         payload = {
#             "borrower_id": b_id, "principal": ln_amt, 
#             "lending_date": str(ln_date), "plan_payback_date": str(ln_payback)
#         }
#         res = post_api("loans/", payload)
#         if res and res.status_code == 200:
#             st.success("Loan Issued & Cash Deducted from Fund!")
#             st.rerun()
#         else:
#             st.error(res.json().get("detail", "Error"))

#     st.divider()
    
#     # 3. Utilities
#     if st.button("⚠️ Refresh All Loan Statuses (Check Overdue)"):
#         res = post_api("loans/refresh-all", {})
#         if res: st.write(res.json()["message"])
