import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Upload Data", "Upload and preview your transaction dataset")
st.markdown("---")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")

    st.success(f"File uploaded successfully — {len(df):,} rows found")

    st.subheader("Preview (first 10 rows)")
    st.dataframe(df.head(10))

    st.subheader("Dataset Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows", f"{len(df):,}")
    col2.metric("Total Columns", len(df.columns))
    col3.metric("Missing Values", f"{df.isnull().sum().sum():,}")
else:
    st.info("Please upload a CSV file to get started.")