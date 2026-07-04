import streamlit as st
import streamlit.components.v1 as components
import json
import os
import hashlib

USERS_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

st.set_page_config(page_title="Retail Analytics Platform", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if not st.session_state.logged_in:

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(ellipse at top left, #1a1f3c 0%, #0F1117 60%); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    margin-bottom: 1.2rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    color: #718096 !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4F8BF9, #7B5CF5) !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(79,139,249,0.4) !important;
}
.stTextInput label {
    color: #A0AEC0 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
}
.stTextInput > div > div > input::placeholder { color: #4A5568 !important; }
.stTextInput > div > div > input:focus {
    border-color: #4F8BF9 !important;
    background: rgba(79,139,249,0.06) !important;
    box-shadow: 0 0 0 3px rgba(79,139,249,0.12) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #4F8BF9 0%, #7B5CF5 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(79,139,249,0.35) !important;
    transition: all 0.2s !important;
    margin-top: 0.5rem !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 25px rgba(79,139,249,0.5) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; font-size: 0.875rem !important; }
</style>
""", unsafe_allow_html=True)

    left, right = st.columns([1.1, 1])

    with left:
        components.html("""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
body {
    background: linear-gradient(160deg, #1a2744 0%, #0f1528 100%);
    min-height: 100vh;
    padding: 3.5rem 2.5rem;
    color: white;
}
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    background: rgba(79,139,249,0.1);
    border: 1px solid rgba(79,139,249,0.25);
    border-radius: 30px;
    padding: 0.4rem 1rem;
    margin-bottom: 2rem;
}
.badge-dot {
    width: 8px; height: 8px;
    background: #4F8BF9;
    border-radius: 50%;
}
.badge-text {
    color: #4F8BF9;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
h1 {
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.25;
    margin-bottom: 1.2rem;
    color: #fff;
}
h1 span {
    background: linear-gradient(135deg, #4F8BF9, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sub {
    color: #718096;
    font-size: 0.95rem;
    line-height: 1.75;
    margin-bottom: 2.5rem;
}
.feature {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.4rem;
}
.icon {
    width: 40px; height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.icon-blue { background: rgba(79,139,249,0.12); border: 1px solid rgba(79,139,249,0.2); }
.icon-purple { background: rgba(123,92,245,0.12); border: 1px solid rgba(123,92,245,0.2); }
.icon-green { background: rgba(72,187,120,0.12); border: 1px solid rgba(72,187,120,0.2); }
.feat-title { color: #E2E8F0; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.2rem; }
.feat-sub { color: #718096; font-size: 0.8rem; }
.stats {
    display: flex;
    gap: 2.5rem;
    margin-top: 2.5rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.stat-num { font-size: 1.5rem; font-weight: 700; color: #fff; }
.stat-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #4A5568;
    margin-top: 0.2rem;
}
</style>
</head>
<body>
<div class="badge">
    <div class="badge-dot"></div>
    <span class="badge-text">Live Analytics Platform</span>
</div>

<h1>Turn transactions into<br><span>actionable insights</span></h1>

<p class="sub">Upload your retail data and instantly discover which products get bought together, who your best customers are, and where your revenue is coming from.</p>

<div class="feature">
    <div class="icon icon-blue">🛒</div>
    <div>
        <div class="feat-title">Market Basket Analysis</div>
        <div class="feat-sub">Apriori & FP-Growth association rule mining</div>
    </div>
</div>

<div class="feature">
    <div class="icon icon-purple">👥</div>
    <div>
        <div class="feat-title">Customer Segmentation</div>
        <div class="feat-sub">RFM scoring with KMeans clustering</div>
    </div>
</div>

<div class="feature">
    <div class="icon icon-green">📈</div>
    <div>
        <div class="feat-title">Sales Dashboard</div>
        <div class="feat-sub">Revenue trends, top products, country breakdown</div>
    </div>
</div>

<div class="stats">
    <div>
        <div class="stat-num">541K+</div>
        <div class="stat-label">Transactions</div>
    </div>
    <div>
        <div class="stat-num">76</div>
        <div class="stat-label">Rules Mined</div>
    </div>
    <div>
        <div class="stat-num">4,338</div>
        <div class="stat-label">Customers</div>
    </div>
</div>
</body>
</html>
""", height=700)

    with right:
        st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)

        st.markdown("""<div style="text-align:center;margin-bottom:2rem;">
<div style="width:58px;height:58px;background:linear-gradient(135deg,#4F8BF9,#7B5CF5);border-radius:16px;display:inline-flex;align-items:center;justify-content:center;font-size:1.6rem;margin-bottom:1rem;box-shadow:0 8px 25px rgba(79,139,249,0.35);">📊</div>
<h2 style="color:#FFFFFF;font-size:1.6rem;font-weight:700;margin:0;">Welcome back</h2>
<p style="color:#718096;font-size:0.875rem;margin:0.4rem 0 0 0;">Sign in to your analytics dashboard</p>
</div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑   Login", "✨   Sign Up"])

        with tab1:
            username = st.text_input("Username", key="login_user", placeholder="your_username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            if st.button("Sign in →", key="login_btn"):
                users = load_users()
                if username in users and users[username] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab2:
            new_username = st.text_input("Username", key="signup_user", placeholder="choose_a_username")
            new_password = st.text_input("Password", type="password", key="signup_pass", placeholder="Min 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Repeat your password")
            if st.button("Create account →", key="signup_btn"):
                if not new_username or not new_password:
                    st.error("Username and password cannot be empty.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    users = load_users()
                    if new_username in users:
                        st.error("Username already taken.")
                    else:
                        users[new_username] = hash_password(new_password)
                        save_users(users)
                        st.success("Account created! Go to Login and sign in.")

    st.stop()

# ── Logged in home page ───────────────────────────────────────────────────
from style import apply_styles, page_header
apply_styles()

page_header("Retail Analytics Platform", f"Welcome back, {st.session_state.current_user}!")

st.markdown("""
### What this app does
This platform analyses retail transaction data to uncover two things:

- **Which products get bought together** — using Association Rule Mining (Apriori & FP-Growth)
- **Which customers are most valuable** — using RFM scoring and KMeans clustering

### How to use it
1. Go to **Upload** in the sidebar — upload your transaction CSV
2. Go to **Market Basket** — see product association rules
3. Go to **Dashboard** — see sales metrics and charts
4. Go to **Segmentation** — see customer segments
""")

st.info("Use the sidebar on the left to navigate between pages.")

with st.sidebar:
    st.markdown(f"Logged in as: **{st.session_state.current_user}**")
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()