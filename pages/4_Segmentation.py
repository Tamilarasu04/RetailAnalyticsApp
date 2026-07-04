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

page_header("Customer Segmentation", "RFM scoring with KMeans clustering")
st.markdown("---")

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_data.csv")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df

df = load_data()

snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df.groupby("CustomerID").agg(
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

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

cluster_summary = rfm.groupby("Cluster").agg(
    Recency=("Recency", "mean"),
    Frequency=("Frequency", "mean"),
    Monetary=("Monetary", "mean"),
    Count=("CustomerID", "count")
).round(1)

cluster_labels = {
    0: "Low Value",
    1: "Premium",
    2: "Regular",
    3: "Dormant"
}
rfm["Segment"] = rfm["Cluster"].map(cluster_labels)

st.subheader("Customer Segments Summary")
st.dataframe(cluster_summary, use_container_width=True)

st.subheader("Segment Distribution")
fig = px.pie(rfm, names="Segment", title="Customers by Segment")
st.plotly_chart(fig, use_container_width=True)

st.subheader("RFM Scatter Plot")
fig2 = px.scatter(rfm, x="Recency", y="Monetary", color="Segment",
                  size="Frequency", hover_data=["CustomerID"],
                  title="Recency vs Monetary Value by Segment")
st.plotly_chart(fig2, use_container_width=True)