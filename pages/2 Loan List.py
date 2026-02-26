import streamlit as st
import pandas as pd
from app import refresh_all_loans # Import the global function

st.title("📂 Loan Portfolio")
if "all_loans" not in st.session_state:
    st.session_state.all_loans = []


# 2. Setup Filters (Radio or Tabs)
view_mode = st.radio("Select View", ["Active Loans", "Closed Loans", "All History"], horizontal=True)

# 3. Logic to "Slice" the Session State data
all_data = st.session_state.all_loans

if all_data:
    if view_mode == "Active Loans":
        # Filter for anything NOT closed ('cl')
        filtered_data = [l for l in all_data if l['status'] != "cl"]
    elif view_mode == "Closed Loans":
        # Filter only for closed ('cl')
        filtered_data = [l for l in all_data if l['status'] == "cl"]
    else:
        filtered_data = all_data

    # 4. Display the Result
    if filtered_data:
        df = pd.DataFrame(filtered_data)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info(f"No {view_mode} found.")
else:
    st.warning("No data available. Please Sync.")