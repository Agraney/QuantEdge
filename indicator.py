import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Download stock data
ticker = "RELIANCE.NS"
data = yf.download(ticker, start="2020-01-01", end="2024-12-31")

### 1. MACD Calculation
ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = ema_12 - ema_26
data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

### 2. RSI Calculation
delta = data['Close'].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()

rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# Drop NA rows created by moving averages
data.dropna(inplace=True)

# Plot
plt.figure(figsize=(12, 6))

# MACD
plt.subplot(2, 1, 1)
plt.plot(data['MACD'], label='MACD')
plt.plot(data['Signal_Line'], label='Signal Line')
plt.title(f"{ticker} - MACD")
plt.legend()

# RSI
plt.subplot(2, 1, 2)
plt.plot(data['RSI'], label='RSI', color='orange')
plt.axhline(70, color='red', linestyle='--', label='Overbought')
plt.axhline(30, color='green', linestyle='--', label='Oversold')
plt.title(f"{ticker} - RSI")
plt.legend()

plt.tight_layout()
plt.savefig("indicators_plot.png")
print("Indicators plotted and saved to indicators_plot.png")
