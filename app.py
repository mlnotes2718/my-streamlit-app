import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
print(f"🟢 Rerun at: {datetime.now()}")

# Sets the page configuration
# You can set the page title and layout here
st.set_page_config(page_title="HDB Resale Dashboard", layout="wide")

st.title("Singapore HDB Resale Dashboard")
st.caption("Code-along: building a usable dashboard from real resale transactions.")

st.header("Dashboard Overview")
st.subheader("What this app will show")
st.markdown("""
- Transaction volume after filtering
- Average resale price
- Median floor area
- Town and flat type trends
""")

DATA_PATH = "./data/resale_data.csv"

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"])
    return df

df = load_data(DATA_PATH)

# Lesson assumption:
# this dataset has already gone through EDA and basic cleaning.
# Here we focus on dashboard building, not data cleaning.
# We still set the datetime dtype explicitly for reliable filtering and charting.
df["month"] = pd.to_datetime(df["month"])

#st.write(f"Rows loaded: {len(df):,} | Columns: {len(df.columns)}")
#st.dataframe(df.head(20), width="stretch")

st.sidebar.header("Filters")

unique_towns = sorted(df["town"].dropna().unique())
unique_flat_types = sorted(df["flat_type"].dropna().unique())

selected_towns = st.sidebar.multiselect("Town", unique_towns, default=[])
selected_flat_types = st.sidebar.multiselect("Flat Type", unique_flat_types, default=[])

min_price = int(df["resale_price"].min())
max_price = int(df["resale_price"].max())
price_range = st.sidebar.slider(
    "Resale Price Range",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=10000,
)

date_min = df["month"].min().date()
date_max = df["month"].max().date()
date_range = st.sidebar.date_input("Month Range", value=(date_min, date_max))

filtered_df = df.copy()

if selected_towns:
    filtered_df = filtered_df[filtered_df["town"].isin(selected_towns)]

if selected_flat_types:
    filtered_df = filtered_df[filtered_df["flat_type"].isin(selected_flat_types)]

filtered_df = filtered_df[
    filtered_df["resale_price"].between(price_range[0], price_range[1])
]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[filtered_df["month"].between(
        pd.to_datetime(start_date), pd.to_datetime(end_date)
    )]

st.header("Filtered Results")
st.write(f"Matching rows: {len(filtered_df):,} | Columns: {len(filtered_df.columns)}")
st.dataframe(filtered_df.head(20), width="stretch")

st.header("Key Metrics")
# Create four columns for the metrics and unpack them
# We can then use each column to place a metric
col1, col2, col3, col4 = st.columns(4)

# Populate each column with a metric by passing label and value
col1.metric("Transactions", f"{len(filtered_df):,}")
col2.metric("Average Price", f"${filtered_df['resale_price'].mean():,.0f}")
col3.metric("Median Price", f"${filtered_df['resale_price'].median():,.0f}")
col4.metric("Median Floor Area", f"{filtered_df['floor_area_sqm'].median():.1f} sqm")

st.header("Visual Analysis")

col_left, col_right = st.columns(2)

# Tells Streamlit to put the following content in the left column
with col_left:
    st.subheader("Average Resale Price by Town")
    avg_price_by_town = (
        filtered_df.groupby("town", as_index=False)["resale_price"]
        .mean()
        .sort_values("resale_price", ascending=False)
        .head(10) # Top 10 towns only for clarity
    )
    # Create a Plotly bar chart with towns on x-axis and average resale price on y-axis
    fig_town = px.bar(avg_price_by_town, x="town", y="resale_price")
    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig_town, width="stretch")

# Tells Streamlit to put the following content in the right column
with col_right:
    st.subheader("Transactions by Flat Type")
    tx_by_flat = (
        filtered_df.groupby("flat_type", as_index=False)
        .size()
        .rename(columns={"size": "transactions"})
        .sort_values("transactions", ascending=False)
    )
    # Create a Plotly bar chart with flat types on x-axis and transaction counts on y-axis
    fig_flat = px.bar(tx_by_flat, x="flat_type", y="transactions")
    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig_flat, width="stretch")

st.subheader("Monthly Median Resale Price")
trend = (
    filtered_df.groupby("month", as_index=False)["resale_price"]
    .median()
    .sort_values("month")
)
# Create a Plotly line chart with month on x-axis and median resale price on y-axis
fig_trend = px.line(trend, x="month", y="resale_price", markers=True)
# Display the Plotly chart in Streamlit
st.plotly_chart(fig_trend, width="stretch")

with st.expander("View Filtered Transactions"):
    st.dataframe(filtered_df, width="stretch", height=350)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv,
        file_name="filtered_resale_data.csv",
        mime="text/csv",
    )