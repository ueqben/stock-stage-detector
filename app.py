import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime
from deep_translator import GoogleTranslator

# Title
st.title("Stock Stage Detector")

# Multi-ticker input
ticker_input = st.text_input("Enter one or more stock tickers (comma-separated):", "AAPL, MSFT, TSLA")
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Store results for summary
summary_data = []

# Enhanced stage classification function
def classify_stage_v2(short_mas, long_mas, short_slope, long_slope):
    above = all(s > l for s, l in zip(short_mas, long_mas))
    below = all(s < l for s, l in zip(short_mas, long_mas))
    near_equal = abs(sum(short_mas)/3 - sum(long_mas)/3) / (sum(long_mas)/3) < 0.01

    if near_equal and abs(short_slope) < 0.1:
        return "Stage 1"
    elif above and short_slope > 0 and long_slope <= 0:
        return "Stage 1 into Stage 2"
    elif above and short_slope > 0 and long_slope > 0:
        return "Stage 2"
    elif above and short_slope <= 0:
        return "Stage 2 into Stage 3"
    elif near_equal and abs(short_slope) < 0.05:
        return "Stage 3"
    elif below and short_slope < 0 and long_slope >= 0:
        return "Stage 3 into Stage 4"
    elif below and short_slope < 0 and long_slope < 0:
        return "Stage 4"
    elif below and short_slope >= 0:
        return "Stage 4 into Stage 1"
    else:
        return "Unclassified"

# Loop through each ticker
for ticker in tickers:
    data = yf.download(ticker, period="90d", interval="1d")

    if data.empty:
        summary_data.append({"Ticker": ticker, "Stage": "No data"})
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
            summary_data.append({"Ticker": ticker, "Stage": "Insufficient data"})
            continue

        short_slope = float(
            latest[['MA_5', 'MA_8', 'MA_13']].mean() - past[['MA_5', 'MA_8', 'MA_13']].mean()
        )
        long_slope = float(
            latest[['MA_50', 'MA_55', 'MA_60']].mean() - past[['MA_50', 'MA_55', 'MA_60']].mean()
        )

        stage = classify_stage_v2(short_mas, long_mas, short_slope, long_slope)
        summary_data.append({"Ticker": ticker, "Stage": stage})

    except Exception as e:
        summary_data.append({"Ticker": ticker, "Stage": f"Error: {str(e)}"})
        continue

# Show summary table
if summary_data:
    st.subheader("Summary of Stock Stages")
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df)

# Optional: Display charts and MAs for each
st.markdown("---")
for row in summary_data:
    ticker = row["Ticker"]
    stage = row["Stage"]
    if stage.startswith("Error") or stage == "No data" or stage == "Insufficient data":
        continue

    st.header(f"{ticker} — {stage}")
    data = yf.download(ticker, period="90d", interval="1d")

    # Recompute MAs
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_8'] = data['Close'].rolling(window=8).mean()
    data['MA_13'] = data['Close'].rolling(window=13).mean()
    data['MA_50'] = data['Close'].rolling(window=50).mean()
    data['MA_55'] = data['Close'].rolling(window=55).mean()
    data['MA_60'] = data['Close'].rolling(window=60).mean()

    st.subheader("Stock Price and Moving Averages")
    fig, ax = plt.subplots()
    data['Close'].plot(ax=ax, label='Close', color='black')
    data['MA_5'].plot(ax=ax, label='MA 5', color='#cce6ff')     # Light blue
    data['MA_8'].plot(ax=ax, label='MA 8', color='#99ccff')     # Medium-light blue
    data['MA_13'].plot(ax=ax, label='MA 13', color='#66b2ff')   # Medium blue
    data['MA_50'].plot(ax=ax, label='MA 50', color='#3399ff')   # Darker blue
    data['MA_55'].plot(ax=ax, label='MA 55', color='#0073e6')   # Even darker blue
    data['MA_60'].plot(ax=ax, label='MA 60', color='#0059b3')   # Very dark blue
    ax.legend()
    st.pyplot(fig)

# Macro news section
st.markdown("---")
st.subheader("Macro & Geopolitical News by Ticker")

api_key = "2891f6cd3c544fb88bd05f8466ace951"
from_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')

for ticker in tickers:
    query = ticker
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&language=en&apiKey={api_key}"

    st.markdown(f"### {ticker} News & Sentiment")
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])[:5]

        if not articles:
            st.write("No relevant news found.")
            continue

        positive_keywords = ["growth", "beat", "recovery", "optimism", "rally"]
        negative_keywords = ["recession", "crisis", "tensions", "decline", "cut"]
        score = 0

        for article in articles:
            title = article["title"]
            try:
                title = GoogleTranslator(source='auto', target='en').translate(title)
            except:
                pass
            st.write(f"- [{title}]({article['url']})")
            lower_title = title.lower()
            if any(word in lower_title for word in positive_keywords):
                score += 1
            elif any(word in lower_title for word in negative_keywords):
                score -= 1

        # Interpret sentiment score
        if score >= 2:
            sentiment = "🟢 Positive sentiment"
        elif score <= -2:
            sentiment = "🔴 Negative sentiment"
        else:
            sentiment = "🟠 Mixed or unclear sentiment"

        st.markdown(f"**Sentiment summary**: {sentiment}")

    except Exception as e:
        st.error(f"Error fetching news for {ticker}: {e}")
