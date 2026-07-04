import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Upload Data", "Upload any retail transaction CSV and map your columns")
st.markdown("---")

# Required columns and their descriptions
REQUIRED_COLUMNS = {
    "InvoiceNo":   "Order/Invoice/Transaction ID",
    "Description": "Product name/description",
    "Quantity":    "Quantity purchased",
    "InvoiceDate": "Date of purchase",
    "UnitPrice":   "Price per unit",
    "CustomerID":  "Customer ID",
    "Country":     "Country (optional but recommended)"
}

def clean_dataframe(df):
    before = len(df)
    df = df.dropna(subset=["CustomerID"])
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed")
    df = df.dropna(subset=["Description"])
    df["Description"] = df["Description"].str.strip()
    after = len(df)
    return df, before, after

# Upload widget
uploaded_file = st.file_uploader(
    "Upload your retail transaction CSV",
    type=["csv"],
    help="Any retail CSV with order/transaction data. You'll map your column names in the next step."
)

if uploaded_file is not None:

    # Try common encodings
    try:
        raw_df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
    except:
        raw_df = pd.read_csv(uploaded_file, encoding="utf-8")

    st.success(f"File loaded — {len(raw_df):,} rows, {len(raw_df.columns)} columns")

    # Show raw preview
    with st.expander("Preview raw data (first 5 rows)"):
        st.dataframe(raw_df.head())

    st.markdown("---")
    st.subheader("Map Your Columns")
    st.markdown("Match your file's column names to what the app expects. Select **Skip** if your file doesn't have that column.")

    user_columns = list(raw_df.columns)
    skip_option = "-- Skip --"
    options = [skip_option] + user_columns

    # Auto-detect columns by fuzzy matching
    def auto_detect(target, columns):
        target_lower = target.lower().replace(" ", "").replace("_", "")
        for col in columns:
            col_clean = col.lower().replace(" ", "").replace("_", "")
            if target_lower in col_clean or col_clean in target_lower:
                return col
        return skip_option

    col1, col2 = st.columns(2)
    mapping = {}

    with col1:
        mapping["InvoiceNo"] = st.selectbox(
            "🧾 Invoice/Order ID",
            options,
            index=options.index(auto_detect("InvoiceNo", user_columns)),
            help="Unique identifier for each transaction/order"
        )
        mapping["Description"] = st.selectbox(
            "📦 Product Description",
            options,
            index=options.index(auto_detect("Description", user_columns)),
            help="Product name or description"
        )
        mapping["Quantity"] = st.selectbox(
            "🔢 Quantity",
            options,
            index=options.index(auto_detect("Quantity", user_columns)),
            help="Number of units purchased"
        )
        mapping["InvoiceDate"] = st.selectbox(
            "📅 Invoice Date",
            options,
            index=options.index(auto_detect("InvoiceDate", user_columns)),
            help="Date of the transaction"
        )

    with col2:
        mapping["UnitPrice"] = st.selectbox(
            "💰 Unit Price",
            options,
            index=options.index(auto_detect("UnitPrice", user_columns)),
            help="Price per unit"
        )
        mapping["CustomerID"] = st.selectbox(
            "👤 Customer ID",
            options,
            index=options.index(auto_detect("CustomerID", user_columns)),
            help="Unique customer identifier"
        )
        mapping["Country"] = st.selectbox(
            "🌍 Country",
            options,
            index=options.index(auto_detect("Country", user_columns)),
            help="Country of the customer (optional)"
        )

    st.markdown("---")

    if st.button("Apply Mapping & Analyse →"):
        # Check required columns are mapped
        required = ["InvoiceNo", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
        missing = [k for k in required if mapping[k] == skip_option]

        if missing:
            st.error(f"Please map these required columns: {missing}")
        else:
            # Build renamed dataframe
            rename_map = {v: k for k, v in mapping.items() if v != skip_option}
            mapped_df = raw_df.rename(columns=rename_map)

            # Add Country column if skipped
            if mapping["Country"] == skip_option:
                mapped_df["Country"] = "Unknown"

            # Keep only needed columns
            mapped_df = mapped_df[list(REQUIRED_COLUMNS.keys())]

            # Clean
            with st.spinner("Cleaning data..."):
                cleaned_df, before, after = clean_dataframe(mapped_df)

            # Save to session state
            st.session_state["uploaded_df"] = cleaned_df
            st.session_state["data_source"] = "uploaded"

            st.success("Data mapped, cleaned and ready for analysis!")

            # Stats
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Raw Rows", f"{before:,}")
            col2.metric("Clean Rows", f"{after:,}")
            col3.metric("Rows Removed", f"{before - after:,}")
            col4.metric("Unique Products", f"{cleaned_df['Description'].nunique():,}")

            st.markdown("---")
            st.subheader("Preview Cleaned Data")
            st.dataframe(cleaned_df.head(10))

            col1, col2, col3 = st.columns(3)
            col1.metric("Unique Invoices", f"{cleaned_df['InvoiceNo'].nunique():,}")
            col2.metric("Unique Customers", f"{cleaned_df['CustomerID'].nunique():,}")
            col3.metric("Countries", f"{cleaned_df['Country'].nunique():,}")

            st.info("Now go to Market Basket, Dashboard, or Segmentation in the sidebar to see your analysis.")

else:
    # Load default if nothing uploaded
    if "uploaded_df" not in st.session_state:
        default_df = pd.read_csv("cleaned_data.csv")
        default_df["InvoiceDate"] = pd.to_datetime(default_df["InvoiceDate"])
        st.session_state["uploaded_df"] = default_df
        st.session_state["data_source"] = "default"

    if st.session_state.get("data_source") == "default":
        st.info("No file uploaded yet — all pages are showing the default Online Retail UK dataset (541K transactions). Upload your own CSV above to analyse your data.")
    else:
        st.success("Using your previously uploaded and mapped dataset. Upload a new file above to switch datasets.")