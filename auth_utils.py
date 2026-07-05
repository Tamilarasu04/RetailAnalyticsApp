import streamlit as st

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = ""

    if not st.session_state.logged_in:
        st.warning("Please log in first.")
        st.stop()

    with st.sidebar:
        st.markdown(f"Logged in as: **{st.session_state.current_user}**")
        st.markdown("---")
        if st.button("Logout", key=f"logout_{__name__}"):
            st.session_state.logged_in = False
            st.session_state.current_user = ""
            st.switch_page("Home.py")