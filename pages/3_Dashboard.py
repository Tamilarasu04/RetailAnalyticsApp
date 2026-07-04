import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_login
from style import apply_styles, page_header

apply_styles()
check_login()

page_header("Sales Dashboard", "Real-time retail performance metrics")
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

# Calculate fields
df["Revenue"] = df["Quantity"] * df["UnitPrice"]
df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)
df["Year"] = df["InvoiceDate"].dt.year

# Metric cards
total_revenue = df["Revenue"].sum()
total_orders = df["InvoiceNo"].nunique()
total_customers = df["CustomerID"].nunique()
avg_order_value = total_revenue / total_orders
total_products = df["Description"].nunique()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Revenue", f"£{total_revenue:,.0f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Total Customers", f"{total_customers:,}")
col4.metric("Avg Order Value", f"£{avg_order_value:,.2f}")
col5.metric("Unique Products", f"{total_products:,}")

st.markdown("---")

# Two column layout for charts
left, right = st.columns(2)

with left:
    st.subheader("Top 10 Products by Revenue")
    top_products = (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.bar(
        top_products,
        x="Revenue",
        y="Description",
        orientation="h",
        color="Revenue",
        color_continuous_scale="Blues",
        title="Top 10 Products"
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Top 10 Countries by Revenue")
    top_countries = (
        df.groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig2 = px.bar(
        top_countries,
        x="Revenue",
        y="Country",
        orientation="h",
        color="Revenue",
        color_continuous_scale="Purples",
        title="Top 10 Countries"
    )
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Monthly revenue trend
st.subheader("Monthly Revenue Trend")
monthly = (
    df.groupby("Month")["Revenue"]
    .sum()
    .reset_index()
)
fig3 = px.line(
    monthly,
    x="Month",
    y="Revenue",
    markers=True,
    color_discrete_sequence=["#4F8BF9"]
)
fig3.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#FFFFFF",
    xaxis=dict(tickangle=45)
)
fig3.update_traces(line_width=2.5)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# Bottom row
left2, right2 = st.columns(2)

with left2:
    st.subheader("Revenue by Day of Week")
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = (
        df.groupby("DayOfWeek")["Revenue"]
        .sum()
        .reindex(day_order)
        .reset_index()
    )
    fig4 = px.bar(
        dow,
        x="DayOfWeek",
        y="Revenue",
        color="Revenue",
        color_continuous_scale="Teal"
    )
    fig4.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig4, use_container_width=True)

with right2:
    st.subheader("Top 10 Customers by Revenue")
    top_customers = (
        df.groupby("CustomerID")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top_customers["CustomerID"] = top_customers["CustomerID"].astype(str)
    fig5 = px.bar(
        top_customers,
        x="Revenue",
        y="CustomerID",
        orientation="h",
        color="Revenue",
        color_continuous_scale="Oranges"
    )
    fig5.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig5, use_container_width=True)

# Download
st.markdown("---")
st.download_button(
    label="Download Cleaned Data as CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="cleaned_data_export.csv",
    mime="text/csv"
)