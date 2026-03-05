import streamlit as st
import requests
import plotly.graph_objects as go
from app import init_session_state, refresh_all_data


init_session_state()

st.set_page_config(page_title="3PPL Fund Manager", layout="centered")


dash_data = st.session_state.get("all_dash", {})

if dash_data:
    # --- 1. Circle (Donut) Chart ---
    labels = [m['name'] for m in dash_data['members']]
    values = [m['current_value'] for m in dash_data['members']]
    
    # Matching your image's purple/pink aesthetic
    colors = ['#9b5de5', '#f15bb5', '#fee440'] 

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.7,
        marker_colors=colors,
        showlegend=False
    )])

    # Center text: Total Fund Value
    fig.update_layout(
        annotations=[dict(text=f"TOTAL FUND<br><b>RM {dash_data['total_valuation']:,.2f}</b>", 
                     x=0.5, y=0.5, font_size=20, showarrow=False)],
        margin=dict(t=0, b=0, l=0, r=0),
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 2. Fund Breakdown List ---
    st.subheader("Fund Breakdown")
    for m in dash_data['members']:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{m['name']}** | RM {m['current_value']:,.2f}")
        col2.write(f"{m['stake_pct']}%")
    
    st.divider()

    # --- 3. Financial Stats ---
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"Active loan amount | **RM {dash_data['total_lent']:,.2f}**")
        st.write(f"Cash at hand | **RM {dash_data['cash_on_hand']:,.2f}**")
        st.write(f"Profit earned | **RM {dash_data['profit_earned']:,.2f}**")
    
    with c2:
        if st.button("Member Withdraw", use_container_width=True):
            st.info("Redirecting to withdraw page...")
        if st.button("See active loan",use_container_width=True):
            st.switch_page("pages/2 Loan List.py")
        if st.button("Add bank Interest", use_container_width=True):
            pass # Link to bank interest form

    # --- 4. Footer Buttons ---
    st.write("---")
    f_col1, f_col2 = st.columns(2)
    f_col1.button("See Ledger", use_container_width=True)
    f_col2.button("Borrow Loan", use_container_width=True, type="primary")


    # Provide a Refresh Button
if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()