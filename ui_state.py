import requests
import streamlit as st

API_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 5


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


def get_api(endpoint, params=None):
    try:
        res = requests.get(
            f"{API_URL}/{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def post_api(endpoint, data):
    try:
        return requests.post(
            f"{API_URL}/{endpoint}",
            json=data,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except Exception:
        return None


def delete_api(endpoint):
    try:
        return requests.delete(f"{API_URL}/{endpoint}", timeout=REQUEST_TIMEOUT_SECONDS)
    except Exception:
        return None


def refresh_all_data():
    """Fetches loans and ledger from DB and saves to state."""
    success = True

    try:
        dashboard_response = get_api("dashboard")
        if dashboard_response is not None:
            st.session_state.all_dash = dashboard_response
        else:
            st.error("Failed to fetch dashboard")
            success = False
    except Exception as e:
        st.error(f"dashboard error: {e}")
        success = False

    try:
        loans_response = get_api("loans")
        if loans_response is not None:
            st.session_state.all_loans = loans_response
        else:
            st.error("Failed to fetch loans")
            success = False
    except Exception as e:
        st.error(f"Loans error: {e}")
        success = False

    try:
        ledger_response = get_api("ledger")
        if ledger_response is not None:
            st.session_state.all_ledger = ledger_response
        else:
            st.error("Failed to fetch ledger")
            success = False
    except Exception as e:
        st.error(f"Ledger error: {e}")
        success = False

    st.session_state.is_synced = success
    return success


def ensure_data_synced():
    """Refresh only if data is marked stale."""
    if not st.session_state.get("is_synced", False):
        return refresh_all_data()
    return True
