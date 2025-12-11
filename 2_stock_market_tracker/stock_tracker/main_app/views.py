from django.shortcuts import render
from django.http import JsonResponse
import requests
import yfinance as yf
import pandas as pd
import json
import numpy as np

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://www.alphavantage.co/query?" 

def stock_chart_view(request):
    if request.method == 'POST':
        SMA_WINDOW = 50
        PERIOD_DAYS = "500d" # Fetch data for last 500 trading days

        # Get stock symbol from the form submission (POST data)
        symbol = request.POST.get('symbol', '').upper()
        
        if not symbol:
            return JsonResponse({'error': 'Please provide a stock symbol.'}, status=400)

        # Using alpha vantage, according to alpha vantage's tutorial
        # function = "TIME_SERIES_DAILY_ADJUSTED"
        # url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&outputsize=compact&apikey={API_KEY}'
        # try:
        #     response = requests.get(url)
        #     response.raise_for_status() # Raise exception for bad status codes
        #     data = response.json()
        #     print("--- Alpha Vantage Response ---")
        #     print(data)
        #     print("----------------------------")
 
        #     if "Error Message" in data:
        #          return JsonResponse({'error': data["Error Message"]}, status=400)
            
        #     if "Note" in data:
        #         rate_limit_msg = "Rate limit exceeded. Please wait a minute before submitting."
        #         return JsonResponse({'error': rate_limit_msg}, status=429) # 429 Too Many Requests
 
        #     time_series = data.get("Time Series (Daily)", {})

        #     dates = list(time_series.keys())
        #     # Get the close price for a simple line chart
        #     closing_prices = [float(time_series[date]['4. close']) for date in dates]

        #     # Reverse data so the chart to order chronologically
        #     dates.reverse()
        #     closing_prices.reverse()

        #     # Return data as JSON for the frontend
        #     return JsonResponse({
        #         'symbol': symbol,
        #         'dates': dates,
        #         'prices': closing_prices
        #     })

        # except requests.RequestException as e:
        #     return JsonResponse({'error': f"API Request Failed: {e}"}, status=500)
        # except Exception as e:
        #     return JsonResponse({'error': f"An unexpected error occurred: {e}"}, status=500)

        # Using yfinance
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch the last 500 days of daily historical data
            data = ticker.history(period=PERIOD_DAYS)

            if data.empty:
                return JsonResponse({'error': f"No data found for symbol {symbol}. It may be an invalid ticker."}, status=404)

            # Process  yfinance data (already cleaned)
            # Use 'Close' prices and format the index (dates) for JavaScript
            dates = data.index.strftime('%Y-%m-%d').tolist()
            adj_close_prices = data['Close'].tolist()

            # Calculate the 50-Day Simple Moving Average (SMA)
            # Use 'Close' column as the adjusted price.
            data['SMA_50'] = data['Close'].rolling(window=SMA_WINDOW).mean()

            # Convert the Series to a list.
            # The SMA column contains 'NaN' values for the first 49 days.
            # Remove the np.nan values to Python's None which will be converted to null by JsonResponse
            sma_prices = data['SMA_50'].replace({np.nan: None}).tolist() 

            # Return data as JSON for frontend
            return JsonResponse({
                'symbol': symbol,
                'dates': dates,
                'adj_close_prices': adj_close_prices,
                'sma_prices': sma_prices
            })

        except Exception as e: 
            return JsonResponse({'error': f"An error occurred while fetching stock data: {e}"}, status=500)
    
    # Handle GET request (initial page load)
    return render(request, 'main_app/index.html')