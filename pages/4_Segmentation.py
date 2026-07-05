import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()
st.set_page_config(page_title="Customer Segmentation", layout="wide")
page_header("Customer Segmentation", "RFM scoring with KMeans clustering")
st.markdown("---")

# Get data from session state
if "uploaded_df" not in st.session_state:
    df = pd.read_csv("cleaned_data.csv")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    st.session_state["uploaded_df"] = df
    st.session_state["data_source"] = "default"

df = st.session_state["uploaded_df"].copy()

if st.session_state.get("data_source") == "default":
    st.info("Showing results from default Online Retail dataset. Upload your own CSV on the Upload page.")
else:
    st.success("Showing results from your uploaded dataset.")

st.markdown("---")

# Number of clusters selector
n_clusters = st.slider(
    "Number of Customer Segments",
    min_value=2,
    max_value=6,
    value=4,
    help="How many groups to divide customers into. 4 is recommended."
)

@st.cache_data(show_spinner=False)
def run_segmentation(data_hash, n_clusters):
    df_seg = st.session_state["uploaded_df"].copy()
    df_seg["Revenue"] = df_seg["Quantity"] * df_seg["UnitPrice"]

    snapshot_date = df_seg["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df_seg.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Revenue", "sum")
    ).reset_index()

    rfm_log = rfm.copy()
    rfm_log["Recency"] = np.log1p(rfm["Recency"])
    rfm_log["Frequency"] = np.log1p(rfm["Frequency"])
    rfm_log["Monetary"] = np.log1p(rfm["Monetary"])

    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log[["Recency", "Frequency", "Monetary"]])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

    # Auto label clusters
    summary = rfm.groupby("Cluster").agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean"),
        Count=("CustomerID", "count")
    ).round(1)

    # Label based on monetary rank
    monetary_rank = summary["Monetary"].rank(ascending=False).astype(int)
    recency_rank = summary["Recency"].rank(ascending=True).astype(int)

    labels_pool = ["Premium", "Regular", "Low Value", "Dormant", "At Risk", "New"]
    cluster_labels = {}
    for cluster in summary.index:
        m_rank = monetary_rank[cluster]
        r_rank = recency_rank[cluster]
        if m_rank == 1:
            cluster_labels[cluster] = "Premium"
        elif r_rank == 1 and m_rank <= 2:
            cluster_labels[cluster] = "Regular"
        elif r_rank == n_clusters:
            cluster_labels[cluster] = "Dormant"
        else:
            remaining = [l for l in labels_pool if l not in cluster_labels.values()]
            cluster_labels[cluster] = remaining[0] if remaining else f"Segment {cluster}"

    rfm["Segment"] = rfm["Cluster"].map(cluster_labels)
    return rfm, summary

with st.spinner("Running segmentation..."):
    data_hash = str(len(df)) + str(n_clusters)
    rfm, summary = run_segmentation(data_hash, n_clusters)

# Segment summary metrics
st.subheader("Segment Overview")
cols = st.columns(len(rfm["Segment"].unique()))
for i, segment in enumerate(rfm["Segment"].unique()):
    seg_data = rfm[rfm["Segment"] == segment]
    cols[i].metric(
        segment,
        f"{len(seg_data):,} customers",
        f"£{seg_data['Monetary'].mean():,.0f} avg spend"
    )

st.markdown("---")

# Two column layout
left, right = st.columns(2)

with left:
    st.subheader("Segment Distribution")
    fig = px.pie(
        rfm,
        names="Segment",
        title="Customers by Segment",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Avg Monetary Value by Segment")
    seg_monetary = rfm.groupby("Segment")["Monetary"].mean().reset_index()
    fig2 = px.bar(
        seg_monetary,
        x="Segment",
        y="Monetary",
        color="Monetary",
        color_continuous_scale="Blues",
        title="Average Spend per Segment"
    )
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Scatter plot
st.subheader("RFM Scatter Plot")
fig3 = px.scatter(
    rfm,
    x="Recency",
    y="Monetary",
    color="Segment",
    size="Frequency",
    hover_data=["CustomerID", "Frequency", "Monetary"],
    title="Recency vs Monetary Value by Segment",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig3.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#FFFFFF"
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# RFM Summary Table
st.subheader("Detailed Segment Summary")
summary_display = summary.copy()
summary_display.index = [rfm[rfm["Cluster"] == i]["Segment"].iloc[0]
                         for i in summary_display.index]
summary_display.index.name = "Segment"
st.dataframe(summary_display, use_container_width=True)

# Download
st.download_button(
    label="Download Segmentation Results as CSV",
    data=rfm.to_csv(index=False).encode("utf-8"),
    file_name="customer_segments.csv",
    mime="text/csv"
)