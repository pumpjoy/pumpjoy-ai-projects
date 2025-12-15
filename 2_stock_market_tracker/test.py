import requests
import os
import pandas as pd
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://www.alphavantage.co/query?" # Or FMP's base URL

def fetch_stock_data(symbol, function_name='TIME_SERIES_DAILY'):
    params = {
        'function': function_name,
        'symbol': symbol,
        'apikey': API_KEY,
        'outputsize': 'compact' # Get the last 100 data points
    }

    response = requests.get(BASE_URL, params=params)
 
    if response.status_code == 200:
        return response.json()
    else:
        # Handle other status codes (e.g., 400 Bad Request, 429 Rate Limit)
        print(f"Error fetching data: HTTP {response.status_code}")
        return None
    
def process_data_to_dataframe(raw_data):
    # --- Isolate the Time Series Data ---
    # Find the key containing the time series (e.g., 'Time Series (Daily)')
    # Use next(iter(...)) to grab the first key in the dictionary, which is often the time series key
    
    # Handle the case where the API key is invalid or data fetch failed
    if 'Time Series (Daily)' not in raw_data and 'Error Message' in raw_data:
        print(f"API Error: {raw_data['Error Message']}")
        return pd.DataFrame()
        
    time_series_key = 'Time Series (Daily)' # Explicitly use the key
    
    if time_series_key not in raw_data:
        # Fallback if the key name is slightly different or unexpected
        time_series_key = next((k for k in raw_data.keys() if 'Time Series' in k), None)
        if time_series_key is None:
             print("Invalid or unexpected stock data format returned.")
             return pd.DataFrame() 

    data = raw_data[time_series_key]
    
    # --- Create DataFrame from the nested dictionary ---
    # The dictionary keys are dates, and values are metrics.
    # Read this into a DataFrame: rows become the dates (index), and columns are the metrics.
    df = pd.DataFrame.from_dict(data, orient='index')
    
    # --- Clean up column names and index ---
    # The existing column names are '1. open', '2. high', etc.
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df.index.name = 'Date'
    df.index = pd.to_datetime(df.index)
    
    # --- Convert to proper data types ---
    for col in df.columns:
        # Convert all financial data columns to numeric (excluding the 'Volume' which is an integer)
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df.sort_index()

def analyze_data(df):
    # Calculate Daily Returns
    df['Daily Return'] = df['Close'].pct_change()
    # Calculate a Simple Moving Average (SMA)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    return df


def visualize_data(df, symbol):
    fig = px.line(df, y=['Close', 'SMA_20'], 
                  title=f'{symbol} Price and 20-Day SMA')
    fig.show()

if __name__ == "__main__":
    ticker = 'TSLA' 
    
    raw_json = fetch_stock_data(ticker)
    
    if raw_json:
        stock_df = process_data_to_dataframe(raw_json)
        
        if not stock_df.empty:
            final_df = analyze_data(stock_df)
            print(f"Displaying first 5 rows of processed data for {ticker}:")
            print(final_df.head())
            
            visualize_data(final_df, ticker)
