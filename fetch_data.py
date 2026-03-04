import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Define stock and timeframe
ticker = "TCS.NS"
start_date = "2025-06-01"
end_date = "2025-06-10"

# Download historical data
data = yf.download(ticker, start=start_date, end=end_date)

# Show top rows
print(data.head())
print(data.describe())

