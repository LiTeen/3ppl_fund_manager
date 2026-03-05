import streamlit as st
import datetime

st.header=("Add Income Record")

income_date = st.date_input("When to record the income")

income_amount = st.number_input("Income Amount", value=None,placeholder="Insert number here")

income_remark = st.text_input("Remark")

col1, col2 = st.columns(2)

with col1: 
    if st.button("CONFIRM", type="primary"):
        payload = {

        }
with col2:
    if st.button("Reset"):
        st.rerun()