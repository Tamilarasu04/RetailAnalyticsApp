import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Market Basket Analysis", "Association rules mined using Apriori & FP-Growth")
st.markdown("---")

@st.cache_data
def load_rules():
    rules = pd.read_csv("basket_rules.csv")
    rules["antecedents"] = rules["antecedents"].str.replace(r"frozenset\({", "", regex=True).str.replace(r"}\)", "", regex=True).str.replace("'", "")
    rules["consequents"] = rules["consequents"].str.replace(r"frozenset\({", "", regex=True).str.replace(r"}\)", "", regex=True).str.replace("'", "")
    return rules

rules = load_rules()

col1, col2, col3 = st.columns(3)
col1.metric("Total Rules Found", len(rules))
col2.metric("Avg Confidence", f"{rules['confidence'].mean():.2f}")
col3.metric("Avg Lift", f"{rules['lift'].mean():.2f}")

st.markdown("---")

st.subheader("Filter Rules")
min_lift = st.slider("Minimum Lift", min_value=1.0, max_value=float(rules["lift"].max()), value=1.0, step=0.5)
filtered = rules[rules["lift"] >= min_lift].sort_values("lift", ascending=False)

st.write(f"Showing {len(filtered)} rules with lift ≥ {min_lift}")

st.subheader("Association Rules")
st.dataframe(
    filtered[["antecedents", "consequents", "support", "confidence", "lift"]].round(3),
    use_container_width=True
)

st.subheader("Top 10 Rules by Lift")
top10 = filtered.head(10).copy()
top10["rule"] = top10["antecedents"] + " → " + top10["consequents"]
st.bar_chart(top10.set_index("rule")["lift"])