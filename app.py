import streamlit as st
import requests

API_URL = "http://localhost:8000"

# Initialize
if "all_loans" not in st.session_state:
    st.session_state.all_loans = []

if "all_ledger" not in st.session_state:
    st.session_state.all_ledger = []

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

# Global function
def refresh_all_loans():
    """Fetches every loan from the DB and saves to state."""
    try:
        response = get_api("loans/all") 
        if response:
            st.session_state.all_loans = response
            return True
        else:
            st.error("Failed to fetch loans")
            return False
    except Exception as e:
        st.error(f"Server Offline: {e}")
        return False

def refresh_all_ledger():
    """Fetches ledger entries from the DB and saves to state."""
    try:
        response = get_api("ledger") 
        if response:
            st.session_state.all_ledger = response
            return True
        else:
            st.error("Failed to fetch ledger")
            return False
    except Exception as e:
        st.error(f"Server Offline: {e}")
        return False

# Initial fetch
if not st.session_state.all_loans:
    refresh_all_loans()
if not st.session_state.all_ledger:
    refresh_all_ledger()


# 1. Provide a Refresh Button
if st.sidebar.button("🔄 Sync with Database"):
    if refresh_all_loans():
        st.success("Synced!")
        st.rerun()