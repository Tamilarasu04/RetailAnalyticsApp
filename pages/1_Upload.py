import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Upload Data", "Upload any retail transaction CSV — we'll figure out the columns")
st.markdown("---")

REQUIRED_COLUMNS = {
    "InvoiceNo":   "Order / Invoice / Transaction ID",
    "Description": "Product name / Item name",
    "Quantity":    "Quantity purchased",
    "InvoiceDate": "Date of purchase",
    "UnitPrice":   "Price per unit",
    "CustomerID":  "Customer ID",
    "Country":     "Country (optional)"
}

# ── Format detector ──────────────────────────────────────────────────────────
def detect_format(df):
    """
    Detects if CSV is:
    - 'basket': each row = one transaction, items listed across columns (no proper headers)
    - 'standard': one row per item with proper column headers
    """
    # Check if column names look like product names (basket format)
    # Basket format: headers are food/product names, not field names
    col_names = [str(c).lower().strip() for c in df.columns]

    # Field name keywords that indicate standard format
    field_keywords = [
        "invoice", "order", "transaction", "bill", "id", "no", "number",
        "date", "time", "quantity", "qty", "price", "cost", "amount",
        "customer", "client", "country", "region", "description", "product",
        "item", "name", "total", "revenue", "store", "shop"
    ]

    # Count how many columns match field keywords
    field_matches = sum(
        1 for col in col_names
        if any(kw in col for kw in field_keywords)
    )

    # If less than 2 columns match field keywords → likely basket format
    if field_matches < 2:
        return "basket"
    return "standard"


# ── Convert basket format to transaction format ──────────────────────────────
def basket_to_transactions(df):
    """
    Converts basket format (each row = transaction, items across columns)
    to standard transaction format (one row per item)
    """
    rows = []
    for invoice_no, row in df.iterrows():
        items = [str(item).strip() for item in row if pd.notna(item) and str(item).strip() != ""]
        for item in items:
            rows.append({
                "InvoiceNo": f"INV{invoice_no + 1:05d}",
                "Description": item.upper(),
                "Quantity": 1,
                "InvoiceDate": pd.Timestamp("2024-01-01"),
                "UnitPrice": 1.0,
                "CustomerID": f"CUST{invoice_no + 1:05d}",
                "Country": "Unknown"
            })
    return pd.DataFrame(rows)


# ── Smart column detector for standard format ────────────────────────────────
def detect_columns(df):
    detection = {}
    scores = {col: {} for col in REQUIRED_COLUMNS}
    sample = df.head(500)

    for col in df.columns:
        series = sample[col].dropna().astype(str)
        if series.empty:
            continue

        col_lower = col.lower().replace(" ", "").replace("_", "").replace("-", "")

        # Keyword boosting (highest priority)
        keyword_map = {
            "InvoiceNo":   ["invoice", "order", "transaction", "bill", "receipt", "billno", "orderno", "transactionid", "orderid"],
            "Description": ["desc", "product", "item", "name", "goods", "sku", "article", "productname", "itemname", "description"],
            "Quantity":    ["qty", "quantity", "count", "units", "pieces", "number", "quant"],
            "InvoiceDate": ["date", "time", "datetime", "when", "day", "period", "invoicedate", "orderdate", "saledate"],
            "UnitPrice":   ["price", "cost", "amount", "value", "rate", "fee", "unitprice", "saleprice", "itemprice"],
            "CustomerID":  ["customer", "client", "user", "buyer", "member", "custid", "customerid", "clientid"],
            "Country":     ["country", "region", "location", "nation", "area", "city", "state"]
        }
        for target, keywords in keyword_map.items():
            if any(col_lower == kw or col_lower.startswith(kw) or kw in col_lower for kw in keywords):
                scores[target][col] = 0.95

        # Date detection
        try:
            parsed = pd.to_datetime(series.head(50), infer_datetime_format=True, errors="coerce")
            date_ratio = parsed.notna().mean()
            if date_ratio > 0.7:
                current = scores["InvoiceDate"].get(col, 0)
                scores["InvoiceDate"][col] = max(current, date_ratio)
        except:
            pass

        # Numeric analysis
        try:
            numeric = pd.to_numeric(series, errors="coerce")
            num_ratio = numeric.notna().mean()
            if num_ratio > 0.7:
                values = numeric.dropna()
                if len(values) > 0:
                    is_int = (values == values.round()).mean() > 0.8
                    median_val = values.median()

                    if is_int and 0 < median_val < 200:
                        current = scores["Quantity"].get(col, 0)
                        scores["Quantity"][col] = max(current, 0.75)

                    has_decimal = (values != values.round()).mean() > 0.1
                    if has_decimal and 0 < median_val < 100000:
                        current = scores["UnitPrice"].get(col, 0)
                        scores["UnitPrice"][col] = max(current, 0.75)

                    unique_ratio = values.nunique() / len(values)
                    if is_int and unique_ratio < 0.5:
                        current = scores["CustomerID"].get(col, 0)
                        scores["CustomerID"][col] = max(current, 0.6)
        except:
            pass

        # Text analysis
        unique_ratio = series.nunique() / len(series)
        avg_len = series.str.len().mean()

        if unique_ratio < 0.5:
            current = scores["InvoiceNo"].get(col, 0)
            scores["InvoiceNo"][col] = max(current, 0.6)

        if unique_ratio > 0.3 and avg_len > 3:
            current = scores["Description"].get(col, 0)
            scores["Description"][col] = max(current, unique_ratio * 0.7)

        if unique_ratio < 0.05 and avg_len > 2:
            current = scores["Country"].get(col, 0)
            scores["Country"][col] = max(current, 0.65)

    # Pick best match per required column (no reuse)
    used_cols = set()
    priority = ["InvoiceDate", "Quantity", "UnitPrice", "CustomerID", "InvoiceNo", "Description", "Country"]
    for target in priority:
        if scores[target]:
            sorted_cols = sorted(scores[target].items(), key=lambda x: x[1], reverse=True)
            for col, score in sorted_cols:
                if col not in used_cols:
                    detection[target] = col
                    used_cols.add(col)
                    break

    return detection


# ── Cleaning ─────────────────────────────────────────────────────────────────
def clean_dataframe(df):
    before = len(df)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df = df.dropna(subset=["CustomerID"])
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed", errors="coerce")
    df = df.dropna(subset=["Description", "InvoiceDate"])
    df["Description"] = df["Description"].str.strip().str.upper()
    after = len(df)
    return df, before, after


# ── Upload widget ─────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload your retail transaction CSV",
    type=["csv"],
    help="Works with any retail CSV — supermarket, electronics, clothing, grocery store, etc. Supports both transaction-level and basket-level formats."
)

if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
    except:
        try:
            raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
        except:
            raw_df = pd.read_csv(uploaded_file, encoding="latin1")

    st.success(f"File loaded — {len(raw_df):,} rows, {len(raw_df.columns)} columns")

    with st.expander("Preview raw data (first 5 rows)"):
        st.dataframe(raw_df.head())

    st.markdown("---")

    # Detect format
    fmt = detect_format(raw_df)

    if fmt == "basket":
        # ── BASKET FORMAT ────────────────────────────────────────────────────
        st.info("📋 Detected **basket format** — each row is one transaction with items listed across columns. Converting automatically...")

        with st.spinner("Converting basket format to transaction format..."):
            converted_df = basket_to_transactions(raw_df)

        st.session_state["uploaded_df"] = converted_df
        st.session_state["data_source"] = "uploaded"
        st.session_state["filename"] = uploaded_file.name
        st.session_state["format"] = "basket"

        st.success(f"Converted successfully — {len(converted_df):,} transaction rows from {len(raw_df):,} baskets")

        col1, col2, col3 = st.columns(3)
        col1.metric("Baskets (Orders)", f"{len(raw_df):,}")
        col2.metric("Total Items", f"{len(converted_df):,}")
        col3.metric("Unique Products", f"{converted_df['Description'].nunique():,}")

        st.markdown("---")
        st.subheader("Preview Converted Data")
        st.dataframe(converted_df.head(10))

        st.warning("Note: Since your CSV has no prices, dates, or customer IDs, the Dashboard and Segmentation pages will show limited data. Market Basket Analysis will work fully.")
        st.info("Navigate to Market Basket in the sidebar to see your association rules.")

    else:
        # ── STANDARD FORMAT ──────────────────────────────────────────────────
        with st.spinner("Analysing your columns..."):
            detected = detect_columns(raw_df)

        st.subheader("Column Detection")
        st.markdown("We automatically detected your columns. Review and adjust if anything looks wrong.")

        detection_count = len([v for v in detected.values()])
        if detection_count >= 5:
            st.success(f"✅ Auto-detected {detection_count}/7 columns successfully")
        elif detection_count >= 3:
            st.warning(f"⚠️ Detected {detection_count}/7 columns — please review below")
        else:
            st.error("Could not auto-detect columns — please map them manually below")

        user_columns = list(raw_df.columns)
        skip_option = "-- Skip --"
        options = [skip_option] + user_columns

        def get_index(detected_col):
            if detected_col and detected_col in options:
                return options.index(detected_col)
            return 0

        col1, col2 = st.columns(2)
        mapping = {}

        with col1:
            mapping["InvoiceNo"] = st.selectbox("🧾 Invoice / Order ID", options, index=get_index(detected.get("InvoiceNo")), help="Unique ID for each transaction")
            mapping["Description"] = st.selectbox("📦 Product Name", options, index=get_index(detected.get("Description")), help="Name of the product sold")
            mapping["Quantity"] = st.selectbox("🔢 Quantity", options, index=get_index(detected.get("Quantity")), help="Number of units purchased")
            mapping["InvoiceDate"] = st.selectbox("📅 Date", options, index=get_index(detected.get("InvoiceDate")), help="Date of the transaction")

        with col2:
            mapping["UnitPrice"] = st.selectbox("💰 Unit Price", options, index=get_index(detected.get("UnitPrice")), help="Price per unit")
            mapping["CustomerID"] = st.selectbox("👤 Customer ID", options, index=get_index(detected.get("CustomerID")), help="Unique customer identifier")
            mapping["Country"] = st.selectbox("🌍 Country", options, index=get_index(detected.get("Country")), help="Country (optional)")

        st.markdown("---")

        if st.button("Analyse →", use_container_width=True):
            required = ["InvoiceNo", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
            missing = [k for k in required if mapping[k] == skip_option]

            if missing:
                st.error(f"Please map these required columns: {missing}")
            else:
                rename_map = {v: k for k, v in mapping.items() if v != skip_option}
                mapped_df = raw_df.rename(columns=rename_map)

                if mapping["Country"] == skip_option:
                    mapped_df["Country"] = "Unknown"

                keep_cols = [c for c in REQUIRED_COLUMNS.keys() if c in mapped_df.columns]
                mapped_df = mapped_df[keep_cols]

                with st.spinner("Cleaning your data..."):
                    try:
                        cleaned_df, before, after = clean_dataframe(mapped_df)
                    except Exception as e:
                        st.error(f"Cleaning failed: {e}")
                        st.stop()

                if after == 0:
                    st.error("No valid rows after cleaning. Please check your column mapping — especially Quantity and Price columns.")
                    st.stop()

                st.session_state["uploaded_df"] = cleaned_df
                st.session_state["data_source"] = "uploaded"
                st.session_state["filename"] = uploaded_file.name
                st.session_state["format"] = "standard"

                st.success("Data cleaned and ready for analysis!")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Raw Rows", f"{before:,}")
                col2.metric("Clean Rows", f"{after:,}")
                col3.metric("Removed", f"{before - after:,}")
                col4.metric("Products", f"{cleaned_df['Description'].nunique():,}")

                st.markdown("---")
                st.subheader("Preview Cleaned Data")
                st.dataframe(cleaned_df.head(10))

                col1, col2, col3 = st.columns(3)
                col1.metric("Unique Orders", f"{cleaned_df['InvoiceNo'].nunique():,}")
                col2.metric("Unique Customers", f"{cleaned_df['CustomerID'].nunique():,}")
                col3.metric("Countries", f"{cleaned_df['Country'].nunique():,}")

                st.info("Navigate to Market Basket, Dashboard, or Segmentation in the sidebar.")

else:
    if "uploaded_df" not in st.session_state:
        default_df = pd.read_csv("cleaned_data.csv")
        default_df["InvoiceDate"] = pd.to_datetime(default_df["InvoiceDate"])
        st.session_state["uploaded_df"] = default_df
        st.session_state["data_source"] = "default"
        st.session_state["format"] = "standard"

    if st.session_state.get("data_source") == "default":
        st.info("No file uploaded yet — showing the default Online Retail UK dataset. Upload your store's CSV above to analyse your own data.")
    else:
        fname = st.session_state.get("filename", "your file")
        st.success(f"Currently analysing: **{fname}**. Upload a new file above to switch datasets.")