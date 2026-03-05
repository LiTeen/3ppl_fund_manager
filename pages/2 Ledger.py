import streamlit as st
from datetime import datetime
from ui_state import ensure_data_synced, init_session_state, refresh_all_data

init_session_state()
ensure_data_synced()
st.title("Recent Transactions")

all_data = st.session_state.get("all_ledger", [])

if all_data:
    categories = sorted({record.get("category", "") for record in all_data if record.get("category")})
    col_filter, col_sort = st.columns(2)

    with col_filter:
        selected_category = st.selectbox("Filter by category", ["All"] + categories)

    with col_sort:
        sort_order = st.selectbox("Sort by date", ["Latest", "Earliest"])

    filtered = all_data
    if selected_category != "All":
        filtered = [r for r in filtered if r.get("category") == selected_category]

    filtered = sorted(
        filtered,
        key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")) if isinstance(x["timestamp"], str) else x["timestamp"],
        reverse=(sort_order == "Latest"),
    )

    for record in filtered:
        col1, col2, col3 = st.columns([0.5, 1, 1])

        with col1:
            st.markdown("### ➕" if record["amount"] >= 0 else "### ➖")

        with col2:
            st.markdown(f"**{record['category']}**")
            st.caption(record.get("remarks", ""))

        with col3:
            amount_str = f"RM {abs(record['amount']):,.2f}"
            if record["amount"] > 0:
                st.markdown(f":green[**{amount_str}**]")
            elif record["amount"] < 0:
                st.markdown(f":red[**{amount_str}**]")

            dt = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00")) if isinstance(record["timestamp"], str) else record["timestamp"]
            st.caption(dt.strftime("%d %b %Y"))
else:
    st.info("No transactions yet.")

if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
