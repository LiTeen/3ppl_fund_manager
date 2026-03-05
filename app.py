import streamlit as st
import requests

API_URL = "http://localhost:8000"


def init_session_state():
    """Ensure shared keys exist for every page in the multipage app."""
    if "all_dash" not in st.session_state:
        st.session_state.all_dash = []

    if "all_loans" not in st.session_state:
        st.session_state.all_loans = []

    if "all_ledger" not in st.session_state:
        st.session_state.all_ledger = []

    if "is_synced" not in st.session_state:
        st.session_state.is_synced = False


init_session_state()


# --- API HELPERS ---
def get_api(endpoint, params=None):
    try:
        res = requests.get(f"{API_URL}/{endpoint}", params=params)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def post_api(endpoint, data):
    try:
        return requests.post(f"{API_URL}/{endpoint}", json=data)
    except Exception:
        return None


def delete_api(endpoint):
    try:
        return requests.delete(f"{API_URL}/{endpoint}")
    except Exception:
        return None


# Global function
def refresh_all_data():
    """Fetches loans and ledger from DB and saves to state."""
    success = True

    try:
        dashboard_response = get_api("dashboard")
        if dashboard_response:
            st.session_state.all_dash = dashboard_response
        else:
            st.error("Failed to fetch dashboard")
            success = False
    except Exception as e:
        st.error(f"dashboard error: {e}")
        success = False

    try:
        loans_response = get_api("loans")
        if loans_response:
            st.session_state.all_loans = loans_response
        else:
            st.error("Failed to fetch loans")
            success = False
    except Exception as e:
        st.error(f"Loans error: {e}")
        success = False

    try:
        ledger_response = get_api("ledger")
        if ledger_response:
            st.session_state.all_ledger = ledger_response
        else:
            st.error("Failed to fetch ledger")
            success = False
    except Exception as e:
        st.error(f"Ledger error: {e}")
        success = False

    st.session_state.is_synced = True
    return success


if not st.session_state.is_synced:
    refresh_all_data()

# Default route "/" goes to Dashboard page.
st.switch_page("pages/1 Dashboard.py")
