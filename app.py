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

    short_mas = [latest['MA_5'], latest['MA_8'], latest['MA_13']]
    long_mas = [latest['MA_50'], latest['MA_55'], latest['MA_60']]
    short_slope = (latest[['MA_5', 'MA_8', 'MA_13']].mean() - past[['MA_5', 'MA_8', 'MA_13']].mean())
    long_slope = (latest[['MA_50', 'MA_55', 'MA_60']].mean() - past[['MA_50', 'MA_55', 'MA_60']].mean())

    # Stage detection logic
    def classify_stage(short_mas, long_mas, short_slope, long_slope):
        if all(s > l for s, l in zip(short_mas, long_mas)) and short_slope > 0 and long_slope > 0:
            return "Markup"
        elif all(s < l for s, l in zip(short_mas, long_mas)) and short_slope < 0 and long_slope < 0:
            return "Markdown"
        elif abs(sum(short_mas)/3 - sum(long_mas)/3) / (sum(long_mas)/3) < 0.01 and abs(short_slope) < 0.1:
            return "Accumulation"
        else:
            return "Distribution"

    stage = classify_stage(short_mas, long_mas, short_slope, long_slope)

    # Display results
    st.subheader(f"Stage: {stage}")
    st.write("Short-Term MAs:", {"MA_5": short_mas[0], "MA_8": short_mas[1], "MA_13": short_mas[2]})
    st.write("Long-Term MAs:", {"MA_50": long_mas[0], "MA_55": long_mas[1], "MA_60": long_mas[2]})

    # Plot
    st.subheader("Stock Price and Moving Averages")
    fig, ax = plt.subplots()
    data['Close'].plot(ax=ax, label='Close')
    data['MA_5'].plot(ax=ax, label='MA 5')
    data['MA_8'].plot(ax=ax, label='MA 8')
    data['MA_13'].plot(ax=ax, label='MA 13')
    data['MA_50'].plot(ax=ax, label='MA 50')
    data['MA_55'].plot(ax=ax, label='MA 55')
    data['MA_60'].plot(ax=ax, label='MA 60')
    ax.legend()
    st.pyplot(fig)
