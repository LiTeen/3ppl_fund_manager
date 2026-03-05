import streamlit as st

from ui_state import ensure_data_synced, init_session_state

init_session_state()

ensure_data_synced()

# Default route "/" goes to Dashboard page.
st.switch_page("pages/1 Dashboard.py")
