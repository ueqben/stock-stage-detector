import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Title
st.title("Stock Stage Detector")

# User input for stock ticker
ticker = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, NVDA):", "AAPL").upper()

# Fetch historical data
data = yf.download(ticker, period="90d", interval="1d")

if data.empty:
    st.error("No data found. Please check the ticker symbol.")
else:
    # Calculate moving averages
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_8'] = data['Close'].rolling(window=8).mean()
    data['MA_13'] = data['Close'].rolling(window=13).mean()
    data['MA_50'] = data['Close'].rolling(window=50).mean()
    data['MA_55'] = data['Close'].rolling(window=55).mean()
    data['MA_60'] = data['Close'].rolling(window=60).mean()

    # Get latest and past values for slope
    latest = data.iloc[-1]
    past = data.iloc[-4] if len(data) >= 4 else latest

    # Convert MAs to floats
    short_mas = [
        float(latest['MA_5']),
        float(latest['MA_8']),
        float(latest['MA_13'])
    ]
    long_mas = [
        float(latest['MA_50']),
        float(latest['MA_55']),
        float(latest['MA_60'])
    ]

    short_slope = float(
        latest[['MA_5', 'MA_8', 'MA_13']].mean() - past[['MA_5', 'MA_8', 'MA_13']].mean()
    )
    long_slope = f_
