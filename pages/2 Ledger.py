import streamlit as st
from datetime import datetime
from ui_state import apply_mobile_layout, delete_api, ensure_data_synced, init_session_state, refresh_all_data

init_session_state()
ensure_data_synced()
apply_mobile_layout()
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

    selected_ids = [
        record["id"]
        for record in filtered
        if st.session_state.get(f"ledger_delete_{record['id']}", False)
    ]

    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])
    with action_col1:
        st.caption(f"Selected: {len(selected_ids)}")
    with action_col2:
        if st.button("Delete Selected", type="primary", use_container_width=True):
            if not selected_ids:
                st.warning("No transactions selected.")
            else:
                deleted = 0
                failed = 0
                for ledger_id in selected_ids:
                    res = delete_api(f"maintenance/ledger/{ledger_id}")
                    if res and res.status_code == 200:
                        deleted += 1
                        st.session_state.pop(f"ledger_delete_{ledger_id}", None)
                    else:
                        failed += 1

                st.session_state.is_synced = False
                refresh_all_data()

                if deleted:
                    st.success(f"Deleted {deleted} transaction(s).")
                if failed:
                    st.error(f"Failed to delete {failed} transaction(s).")
                st.rerun()
    with action_col3:
        if st.button("Back to Dashboard", use_container_width=True):
            st.switch_page("dashboard.py")

    for record in filtered:
        col0, col1, col2, col3 = st.columns([0.55, 0.5, 1, 1])

        with col0:
            st.checkbox(
                "Select",
                key=f"ledger_delete_{record['id']}",
                label_visibility="collapsed",
            )

        with col1:
            st.markdown("### +" if record["amount"] >= 0 else "### -")

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

if st.sidebar.button("Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()

