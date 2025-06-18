import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Title
st.title("Stock Stage Detector")

# Multi-ticker input
ticker_input = st.text_input("Enter one or more stock tickers (comma-separated):", "AAPL, MSFT, TSLA")
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Function to classify stage
def classify_stage(short_mas, long_mas, short_slope, long_slope):
    if all(s > l for s, l in zip(short_mas, long_mas)) and short_slope > 0 and long_slope > 0:
        return "Markup"
    elif all(s < l for s, l in zip(short_mas, long_mas)) and short_slope < 0 and long_slope < 0:
        return "Markdown"
    elif abs(sum(short_mas)/3 - sum(long_mas)/3) / (sum(long_mas)/3) < 0.01 and abs(short_slope) < 0.1:
        return "Accumulation"
    else:
        return "Distribution"

# Loop through each ticker
for ticker in tickers:
    st.header(f"{ticker}")
    data = yf.download(ticker, period="90d", interval="1d")

    if data.empty:
        st.error(f"No data found for {ticker}. Please check the symbol.")
        continue

    # Calculate moving averages
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_8'] = data['Close'].rolling(window=8).mean()
    data['MA_13'] = data['Close'].rolling(window=13).mean()
    data['MA_50'] = data['Close'].rolling(window=50).mean()
    data['MA_55'] = data['Close'].rolling(window=55).mean()
    data['MA_60'] = data['Close'].rolling(window=60).mean()

    latest = data.iloc[-1]
    past = data.iloc[-4] if len(data) >= 4 else latest

    try:
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

        if any(pd.isna(val) for val in short_mas + long_mas):
            st.warning("Not enough data to compute all moving averages.")
            continue

        short_slope = float(
            latest[['MA_5', 'MA_8', 'MA_13']].mean() - past[['MA_5', 'MA_8', 'MA_13']].mean()
        )
        long_slope = float(
            latest[['MA_50', 'MA_55', 'MA_60']].mean() - past[['MA_50', 'MA_55', 'MA_60']].mean()
        )

        stage = classify_stage(short_mas, long_mas, short_slope, long_slope)

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

    except Exception as e:
        st.error(f"Error processing {ticker}: {e}")
