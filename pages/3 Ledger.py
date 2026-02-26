import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Recent Transactions")

# Initialize session state
if "all_ledger" not in st.session_state:
    st.session_state.all_ledger = []

all_data = st.session_state.all_ledger

# Custom ledger display
if all_data:
    for record in all_data:
        col1, col2, col3 = st.columns([0.5, 1, 1])
        
        # Column 1: Icon based on amount
        with col1:
            if record["amount"] >= 0:
                #st.markdown(":green[:+1:]")
                st.markdown("### ➕")
            else:
                st.markdown("### ➖")
        
        # Column 2: Category and Remark
        with col2:
            st.markdown(f"**{record['category']}**")
            st.caption(record.get('remarks', ''))
        
        # Column 3: Amount and Date
        with col3:
            if record["amount"] > 0:
                amount_str = f"RM {abs(record['amount']):,.2f}"
                st.markdown(f":green[**{amount_str}**]")
            elif record["amount"] < 0:
                amount_str = f"RM {abs(record['amount']):,.2f}"
                st.markdown(f":red[**{amount_str}**]")

            # Format date
            if isinstance(record['timestamp'], str):
                dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            else:
                dt = record['timestamp']
            date_str = dt.strftime("%d %b %Y")
            st.caption(date_str)
        
       
        #st.divider()
else:
    st.info("No transactions yet.")