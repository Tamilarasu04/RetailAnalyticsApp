import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global */
        * { font-family: 'Inter', sans-serif; }

        /* Main background */
        .stApp {
            background-color: #0F1117;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #161B27;
            border-right: 1px solid #2D3748;
        }
        [data-testid="stSidebar"] .stMarkdown p {
            color: #A0AEC0;
            font-size: 0.85rem;
        }

        /* Sidebar nav links */
        [data-testid="stSidebarNav"] a {
            color: #A0AEC0 !important;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.2s;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: #2D3748;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background-color: #4F8BF9 !important;
            color: #FFFFFF !important;
        }

        /* Page title */
        h1 {
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1.8rem;
            padding-bottom: 0.5rem;
        }

        /* Section headers */
        h2, h3 {
            color: #E2E8F0;
            font-weight: 600;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #1A2035, #1E2744);
            border: 1px solid #2D3748;
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        [data-testid="stMetricLabel"] {
            color: #A0AEC0 !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #4F8BF9, #3B6FD4);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(79,139,249,0.3);
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #3B6FD4, #2855B0);
            box-shadow: 0 4px 8px rgba(79,139,249,0.4);
            transform: translateY(-1px);
        }

        /* Input fields */
        .stTextInput > div > div > input {
            background-color: #1E2130;
            border: 1px solid #2D3748;
            border-radius: 8px;
            color: #FFFFFF;
            padding: 0.6rem 1rem;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4F8BF9;
            box-shadow: 0 0 0 2px rgba(79,139,249,0.2);
        }

        /* Dataframe / tables */
        [data-testid="stDataFrame"] {
            border: 1px solid #2D3748;
            border-radius: 10px;
            overflow: hidden;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #161B27;
            border-radius: 10px;
            padding: 4px;
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            color: #A0AEC0;
            font-weight: 500;
            padding: 0.5rem 1.5rem;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4F8BF9 !important;
            color: #FFFFFF !important;
        }

        /* Info / success / error boxes */
        [data-testid="stInfo"] {
            background-color: rgba(79,139,249,0.1);
            border: 1px solid rgba(79,139,249,0.3);
            border-radius: 8px;
        }
        [data-testid="stSuccess"] {
            background-color: rgba(72,187,120,0.1);
            border: 1px solid rgba(72,187,120,0.3);
            border-radius: 8px;
        }
        [data-testid="stError"] {
            background-color: rgba(245,101,101,0.1);
            border: 1px solid rgba(245,101,101,0.3);
            border-radius: 8px;
        }

        /* Slider */
        .stSlider [data-baseweb="slider"] {
            padding: 0.5rem 0;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background-color: #1E2130;
            border: 2px dashed #2D3748;
            border-radius: 12px;
            padding: 1rem;
            transition: all 0.2s;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: #4F8BF9;
        }

        /* Divider */
        hr {
            border-color: #2D3748;
            margin: 1rem 0;
        }

        /* Remove top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=""):
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1A2035, #1E2744);
            border: 1px solid #2D3748;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        ">
            <h1 style="margin:0; color:#FFFFFF; font-size:1.6rem;">{title}</h1>
            <p style="margin:0.3rem 0 0 0; color:#A0AEC0; font-size:0.9rem;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)