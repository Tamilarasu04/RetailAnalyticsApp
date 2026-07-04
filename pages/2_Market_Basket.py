import streamlit as st
import pandas as pd
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Market Basket Analysis", "Association rules mined using Apriori & FP-Growth")
st.markdown("---")

# Get data from session state
if "uploaded_df" not in st.session_state:
    df = pd.read_csv("cleaned_data.csv")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    st.session_state["uploaded_df"] = df
    st.session_state["data_source"] = "default"

df = st.session_state["uploaded_df"]

if st.session_state.get("data_source") == "default":
    st.info("Showing results from default Online Retail dataset. Upload your own CSV on the Upload page.")
else:
    st.success("Showing results from your uploaded dataset.")

st.markdown("---")

# Algorithm selector
algo = st.radio("Select Algorithm", ["Apriori", "FP-Growth"], horizontal=True)

# Support slider
min_support = st.slider(
    "Minimum Support",
    min_value=0.01,
    max_value=0.1,
    value=0.02,
    step=0.01,
    help="How often an itemset must appear across all baskets. Lower = more rules but slower."
)

@st.cache_data(show_spinner=False)
def run_analysis(data_hash, algo, min_support):
    # Build basket matrix
    basket = (
        df.groupby(["InvoiceNo", "Description"])["Quantity"]
        .sum()
        .unstack()
        .fillna(0)
    )
    basket_sets = basket > 0

    # Run selected algorithm
    if algo == "Apriori":
        frequent_itemsets = apriori(
            basket_sets, min_support=min_support, use_colnames=True
        )
    else:
        frequent_itemsets = fpgrowth(
            basket_sets, min_support=min_support, use_colnames=True
        )

    if len(frequent_itemsets) == 0:
        return None

    rules = association_rules(
        frequent_itemsets, metric="lift", min_threshold=1.0
    )
    rules = rules.sort_values("lift", ascending=False)

    # Clean frozenset display
    rules["antecedents"] = rules["antecedents"].apply(
        lambda x: ", ".join(list(x))
    )
    rules["consequents"] = rules["consequents"].apply(
        lambda x: ", ".join(list(x))
    )
    return rules

# Run analysis with spinner
with st.spinner(f"Running {algo}... this may take 20-40 seconds on large datasets"):
    data_hash = str(len(df)) + algo + str(min_support)
    rules = run_analysis(data_hash, algo, min_support)

if rules is None:
    st.warning("No rules found. Try lowering the minimum support value.")
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rules Found", len(rules))
    col2.metric("Avg Confidence", f"{rules['confidence'].mean():.2f}")
    col3.metric("Avg Lift", f"{rules['lift'].mean():.2f}")

    st.markdown("---")

    # Lift filter
    st.subheader("Filter Rules")
    min_lift = st.slider(
        "Minimum Lift",
        min_value=1.0,
        max_value=float(rules["lift"].max()),
        value=1.0,
        step=0.5
    )
    filtered = rules[rules["lift"] >= min_lift]
    st.write(f"Showing {len(filtered)} rules with lift ≥ {min_lift}")

    # Rules table
    st.subheader("Association Rules")
    st.dataframe(
        filtered[["antecedents", "consequents", "support", "confidence", "lift"]].round(3),
        use_container_width=True
    )

    # Top 10 chart
    st.subheader("Top 10 Rules by Lift")
    top10 = filtered.head(10).copy()
    top10["rule"] = top10["antecedents"] + " → " + top10["consequents"]
    st.bar_chart(top10.set_index("rule")["lift"])

    # Download
    st.download_button(
        label="Download Rules as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="association_rules.csv",
        mime="text/csv"
    )