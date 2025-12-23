import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(page_title="Crypto Hype Monitor", layout="wide")
st.title("📈 BTC Price vs. Social Hype")

# --- Auto-refresh every 5 seconds --- 
st.empty() 
st.info("Refreshing every 5 seconds...")

# Database connection
def get_data():
    conn = psycopg2.connect(
        host="localhost",
        database="hype_db",
        user="user", 
        password="password" 
    )
    query = "SELECT * FROM realtime_hype ORDER BY time DESC LIMIT 100"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.sort_values('time')

# Load the data
df = get_data()

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add Price Trace (Gold Line)
fig.add_trace(
    go.Scatter(x=df['time'], y=df['avg_price'], name="BTC Price", line=dict(color="#FFD700", width=3)),
    secondary_y=False,
)

# Add Hype Trace (Blue Area)
fig.add_trace(
    go.Scatter(x=df['time'], y=df['hype_score'], name="Hype Score", line=dict(color="#00ced1"), fill='tozeroy'),
    secondary_y=True,
)

# Layout adjustments
fig.update_layout(
    height=600,
    title_text="Real-time Correlation: BTC Price and Social Sentiment",
    xaxis_title="Time",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig.update_yaxes(title_text="<b>Price</b> (USD)", secondary_y=False)
fig.update_yaxes(title_text="<b>Hype Score</b> (0.0 - 1.0)", secondary_y=True)

# Display the chart with a unique key to prevent the error
st.plotly_chart(fig, use_container_width=True, key="crypto_chart")

# Display metrics
col1, col2 = st.columns(2)
if not df.empty:
    col1.metric("Current BTC Price", f"${df['avg_price'].iloc[-1]:,.2f}")
    col2.metric("Current Sentiment Score", f"{df['hype_score'].iloc[-1]:.2f}")

# This tells Streamlit to rerun the script automatically
st.button("Manual Refresh") # Optional manual refresh button

# Autorefresh every 5 seconds
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=5000, key="datarefresh")