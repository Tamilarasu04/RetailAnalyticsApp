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

# ── Load data ──────────────────────────────────────────────────────────────
if "uploaded_df" not in st.session_state:
    try:
        df = pd.read_csv("cleaned_data.csv")
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
        st.session_state["uploaded_df"] = df
        st.session_state["data_source"] = "default"
    except Exception as e:
        st.error(f"Could not load default dataset: {e}")
        st.stop()

df = st.session_state["uploaded_df"].copy()

if st.session_state.get("data_source") == "default":
    st.info("Showing results from default Online Retail dataset. Upload your own CSV on the Upload page.")
else:
    st.success("Showing results from your uploaded dataset.")

st.markdown("---")

# ── Settings ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 2])
with col1:
    algo = st.radio(
        "Select Algorithm",
        ["Apriori", "FP-Growth"],
        help="Apriori is classic. FP-Growth is faster on large datasets."
    )
with col2:
    min_support = st.slider(
        "Minimum Support",
        min_value=0.001,
        max_value=0.1,
        value=0.02,
        step=0.001,
        format="%.3f",
        help="Lower = more rules but slower. App auto-retries at lower values if no rules found."
    )

st.markdown("---")


# ── Detect list format ─────────────────────────────────────────────────────
def is_list_format(data):
    if "Description" not in data.columns:
        return False
    sample = data["Description"].dropna().head(20).astype(str)
    return sample.str.strip().str.startswith("[").mean() > 0.5


# ── Parse list products ────────────────────────────────────────────────────
def parse_list_products(data):
    st.info("📋 Detected list-format products — expanding automatically...")

    MAX_BASKETS = 10000
    if len(data) > MAX_BASKETS:
        st.warning(f"Large dataset — sampling {MAX_BASKETS:,} baskets for analysis.")
        data = data.sample(n=MAX_BASKETS, random_state=42).reset_index(drop=True)

    def clean_and_split(val):
        try:
            val = str(val).strip().strip("[]").replace("'", "").replace('"', "")
            return [i.strip().upper() for i in val.split(",") if i.strip()]
        except:
            return []

    data = data.copy()
    data["_items"] = data["Description"].astype(str).apply(clean_and_split)
    expanded = data.explode("_items").copy()
    expanded["Description"] = expanded["_items"].str.strip().str.upper()
    expanded = expanded.drop(columns=["_items"])
    expanded = expanded[
        expanded["Description"].notna() &
        (expanded["Description"] != "") &
        (expanded["Description"] != "NAN") &
        (expanded["Description"] != "NONE")
    ].reset_index(drop=True)

    # Ensure Quantity = 1 for expanded rows
    expanded["Quantity"] = 1

    st.success(f"✅ Expanded {len(data):,} baskets → {len(expanded):,} item rows")
    return expanded


# ── Main analysis ──────────────────────────────────────────────────────────
def run_analysis(data, algo, min_support):

    # Step 1: Parse list-format products
    if is_list_format(data):
        data = parse_list_products(data)

    # Step 2: Validate columns
    if "InvoiceNo" not in data.columns or "Description" not in data.columns:
        st.error("Missing required columns. Please re-upload and map your columns correctly.")
        return None

    if "Quantity" not in data.columns:
        data["Quantity"] = 1

    # Step 3: Clean
    data = data.copy()
    data["Description"] = data["Description"].astype(str).str.strip().str.upper()
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(1)
    data = data[
        data["Description"].notna() &
        (data["Description"] != "") &
        (data["Description"] != "NAN")
    ]

    # Step 4: Check sufficiency
    n_invoices = data["InvoiceNo"].nunique()
    n_products = data["Description"].nunique()

    st.write(f"Processing **{n_invoices:,}** orders × **{n_products:,}** unique products...")

    if n_invoices < 5:
        st.error("Need at least 5 orders to find associations.")
        return None
    if n_products < 2:
        st.error("Need at least 2 unique products to find associations.")
        return None

    # Step 5: Cap products
    MAX_PRODUCTS = 500
    if n_products > MAX_PRODUCTS:
        st.warning(f"Using top {MAX_PRODUCTS} most common products.")
        top_products = data["Description"].value_counts().head(MAX_PRODUCTS).index
        data = data[data["Description"].isin(top_products)]

    # Step 6: Build basket matrix
    try:
        basket = (
            data.groupby(["InvoiceNo", "Description"])["Quantity"]
            .sum()
            .unstack()
            .fillna(0)
        )
        basket_sets = basket > 0
    except MemoryError:
        st.error("Memory error. Try uploading a smaller dataset.")
        return None
    except Exception as e:
        st.error(f"Error building basket: {e}")
        return None

    # Step 7: Try each support level — stop when RULES are found (not just itemsets)
    # This is critical: itemsets exist at high support but produce 0 rules
    # We need to keep lowering support until rules appear
    support_levels = sorted(set([
        min_support, 0.01, 0.005, 0.003, 0.002, 0.001
    ]), reverse=True)

    best_rules = None
    used_support = min_support

    for support in support_levels:
        try:
            if algo == "Apriori":
                fi = apriori(basket_sets, min_support=support, use_colnames=True)
            else:
                fi = fpgrowth(basket_sets, min_support=support, use_colnames=True)

            if fi is None or len(fi) == 0:
                continue

            # Try to generate rules at this support level
            try:
                rules = association_rules(fi, metric="lift", min_threshold=1.0)
                if len(rules) > 0:
                    best_rules = rules
                    used_support = support
                    if support < min_support:
                        st.info(f"Auto-adjusted support to {support:.3f} to find results.")
                    break
            except Exception:
                pass

        except MemoryError:
            st.error("Memory error during analysis. Try increasing Minimum Support.")
            return None
        except Exception:
            continue

    # If no lift>1 rules found anywhere, try confidence fallback at lowest support
    if best_rules is None or len(best_rules) == 0:
        try:
            if algo == "Apriori":
                fi_low = apriori(basket_sets, min_support=0.001, use_colnames=True)
            else:
                fi_low = fpgrowth(basket_sets, min_support=0.001, use_colnames=True)

            if fi_low is not None and len(fi_low) > 0:
                rules_conf = association_rules(fi_low, metric="confidence", min_threshold=0.05)
                rules_conf = rules_conf[rules_conf["lift"] >= 0.5]
                if len(rules_conf) > 0:
                    best_rules = rules_conf
                    st.info("Note: Showing confidence-based rules (weak associations in this dataset).")
        except Exception:
            pass

    if best_rules is None or len(best_rules) == 0:
        st.warning("No meaningful association rules found. Products appear to be purchased independently in this dataset.")
        return None

    # Step 8: Sort and clean display
    best_rules = best_rules.sort_values("lift", ascending=False)

    try:
        best_rules["antecedents"] = best_rules["antecedents"].apply(
            lambda x: ", ".join(sorted(list(x)))
        )
        best_rules["consequents"] = best_rules["consequents"].apply(
            lambda x: ", ".join(sorted(list(x)))
        )
    except Exception:
        pass

    best_rules = best_rules.fillna(0)
    return best_rules


# ── Run ────────────────────────────────────────────────────────────────────
with st.spinner(f"Running {algo}... this may take 20-60 seconds"):
    rules = run_analysis(df, algo, min_support)


# ── Display ────────────────────────────────────────────────────────────────
if rules is not None and len(rules) > 0:

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rules Found", len(rules))
    avg_conf = rules["confidence"].mean()
    avg_lift = rules["lift"].mean()
    col2.metric("Avg Confidence", f"{avg_conf:.2f}" if not pd.isna(avg_conf) else "N/A")
    col3.metric("Avg Lift", f"{avg_lift:.2f}" if not pd.isna(avg_lift) else "N/A")

    st.markdown("---")

    # Safe lift filter slider
    st.subheader("Filter Rules")
    try:
        max_lift = float(rules["lift"].max())
        min_lift_possible = float(rules["lift"].min())

        if max_lift > min_lift_possible and not pd.isna(max_lift):
            step = max(round((max_lift - min_lift_possible) / 20, 3), 0.001)
            min_lift = st.slider(
                "Minimum Lift",
                min_value=round(min_lift_possible, 3),
                max_value=round(max_lift, 3),
                value=round(min_lift_possible, 3),
                step=step,
                format="%.3f"
            )
        else:
            min_lift = min_lift_possible if not pd.isna(min_lift_possible) else 0.0
            st.info(f"All rules have lift ≈ {max_lift:.3f}")
    except Exception:
        min_lift = 0.0

    filtered = rules[rules["lift"] >= min_lift].copy()

    if len(filtered) == 0:
        st.warning("No rules match this filter. Try lowering the Minimum Lift value.")
    else:
        st.write(f"Showing **{len(filtered)}** rules with lift ≥ {min_lift:.3f}")

        st.subheader("Association Rules")
        display_cols = ["antecedents", "consequents", "support", "confidence", "lift"]
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[display_cols].round(3),
            use_container_width=True
        )

        if len(filtered) >= 2:
            st.subheader("Top 10 Rules by Lift")
            top10 = filtered.head(10).copy()
            top10["rule"] = top10["antecedents"] + " → " + top10["consequents"]
            try:
                st.bar_chart(top10.set_index("rule")["lift"])
            except Exception:
                st.dataframe(top10[["rule", "lift"]])

        st.markdown("---")

        try:
            st.download_button(
                label="⬇ Download Rules as CSV",
                data=filtered.to_csv(index=False).encode("utf-8"),
                file_name="association_rules.csv",
                mime="text/csv"
            )
        except Exception:
            pass