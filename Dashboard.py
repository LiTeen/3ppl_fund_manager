import streamlit as st
import plotly.graph_objects as go
from datetime import date
from ui_state import ensure_data_synced, get_api, init_session_state, post_api, refresh_all_data

init_session_state()
ensure_data_synced()

st.set_page_config(page_title="3PPL Fund Manager", layout="centered")

if "show_member_withdraw" not in st.session_state:
    st.session_state.show_member_withdraw = False

dash_data = st.session_state.get("all_dash", {})
ledger_data = st.session_state.get("all_ledger", [])

if dash_data:
    capital_in = sum(
        float(entry.get("amount", 0.0))
        for entry in ledger_data
        if entry.get("category") == "capital_in"
    )
    profit = sum(
        float(entry.get("amount", 0.0))
        for entry in ledger_data
        if entry.get("category") in ("bank_int_received", "loan_int_received")
    )
    expense = sum(
        float(entry.get("amount", 0.0))
        for entry in ledger_data
        if entry.get("category") in ("expense_out", "capital_withdraw")
    )

    composed_total = capital_in + profit + expense
    total_display = composed_total if ledger_data else float(dash_data.get("total_valuation", 0.0))

    labels = ["Capital In", "Profit", "Expense"]
    values = [max(capital_in, 0.0), max(profit, 0.0), abs(expense)]
    if sum(values) <= 0:
        values = [1.0, 0.0, 0.0]

    colors = ["#3a86ff", "#2ec4b6", "#ff6b6b"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.7,
                marker_colors=colors,
                showlegend=True,
            )
        ]
    )

    fig.update_layout(
        annotations=[
            dict(
                text=f"TOTAL FUND<br><b>RM {total_display:,.2f}</b>",
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False,
            )
        ],
        margin=dict(t=0, b=0, l=0, r=0),
        height=320,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Capital In (RM {capital_in:,.2f}) + Profit (RM {profit:,.2f}) + Expense (RM {expense:,.2f}) = RM {total_display:,.2f}"
    )

    st.subheader("Fund Breakdown")
    for m in dash_data["members"]:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{m['name']}** | RM {m['current_value']:,.2f}")
        col2.write(f"{m['stake_pct']}%")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"Active loan amount | **RM {dash_data['total_lent']:,.2f}**")
        st.write(f"Cash at hand | **RM {dash_data['cash_on_hand']:,.2f}**")
        st.write(f"Profit earned | **RM {dash_data['profit_earned']:,.2f}**")

    with c2:
        if st.button("Member Withdraw", use_container_width=True):
            st.session_state.show_member_withdraw = True
        if st.button("Maintenance", use_container_width=True):
            st.switch_page("pages/5 Maintenance.py")

    if st.session_state.show_member_withdraw:
        st.divider()
        st.subheader("Member Withdrawal")

        members = get_api("members") or []
        withdraw_members = [m for m in members if m.get("id", 0) < 4 and m.get("is_active", True)]
        member_options = {
            f"{m['name']} | Capital RM {float(m.get('initial_capital', 0.0)):,.2f}": int(m["id"])
            for m in withdraw_members
        }

        if not member_options:
            st.info("No active member available for withdrawal.")
        else:
            selected_member_label = st.selectbox("Member", list(member_options.keys()))
            selected_member_id = member_options[selected_member_label]
            withdraw_date = st.date_input("Withdrawal Date", value=date.today(), key="member_withdraw_date")
            amount = st.number_input(
                "Withdrawal Amount (RM)",
                min_value=0.0,
                max_value=max(0.0, float(dash_data.get("cash_on_hand", 0.0))),
                value=0.0,
                step=50.0,
                key="member_withdraw_amount",
            )

            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if st.button("Submit Withdrawal", type="primary", use_container_width=True):
                    if amount <= 0:
                        st.error("Withdrawal amount must be greater than 0.")
                    else:
                        payload = {
                            "member_id": selected_member_id,
                            "amount": amount,
                            "date": withdraw_date.isoformat(),
                        }
                        res = post_api("members/withdraw", payload)
                        if res and res.status_code == 200:
                            st.success("Withdrawal recorded.")
                            st.session_state.show_member_withdraw = False
                            st.session_state.is_synced = False
                            refresh_all_data()
                            st.rerun()
                        elif res:
                            st.error(res.json().get("detail", "Withdrawal failed."))
                        else:
                            st.error("Server connection error.")
            with act_col2:
                if st.button("Cancel Withdrawal", use_container_width=True):
                    st.session_state.show_member_withdraw = False
                    st.rerun()

    st.write("---")
    f_col1, f_col2 = st.columns(2)
    if f_col1.button("Add Interest/Expense", use_container_width=True):
        st.switch_page("pages/4 Record Income Expense.py")
    if f_col2.button("Borrow / Repay Loan", use_container_width=True, type="primary"):
        st.switch_page("pages/3 Borrow Repay Loan.py")

if st.sidebar.button("Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
