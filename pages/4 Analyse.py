import streamlit as st
import pandas as pd
from ui_state import ensure_data_synced, get_api, init_session_state, refresh_all_data

init_session_state()
ensure_data_synced()

st.title("Analyse")
st.caption("Borrower summary up to date")

analysis_data = get_api("analyse/borrowers") or []

if analysis_data:
    df = pd.DataFrame(analysis_data)
    df = df.rename(columns={
        "borrower_name": "Borrower",
        "loan_count": "Times Borrowed",
        "interest_contributed": "Interest Contributed (RM)",
    })
    st.dataframe(df[["Borrower", "Times Borrowed", "Interest Contributed (RM)"]], use_container_width=True, hide_index=True)

    st.subheader("Highlights")
    for row in analysis_data:
        st.write(
            f"**{row['borrower_name']}** have borrow **{row['loan_count']}** times, "
            f"contributing **RM {row['interest_contributed']:,.2f}** interest."
        )
else:
    st.info("No borrower data found.")

if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_data():
        st.success("Synced!")
        st.rerun()
