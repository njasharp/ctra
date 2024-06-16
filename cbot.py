import streamlit as st
import pandas as pd
import ccxt
import time

# Set up the Streamlit app
st.title("Crypto Trading Bot")

# Sidebar for user input
st.sidebar.header("User Input")

# Exchange and API keys (replace with your own)
exchange_name = st.sidebar.selectbox("Select Exchange", ["binance", "coinbasepro"])
api_key = st.sidebar.text_input("API Key")
api_secret = st.sidebar.text_input("API Secret", type="password")

# Trading parameters
symbol = st.sidebar.text_input("Trading Pair", value="BTC/USDT")
short_window = st.sidebar.number_input("Short Moving Average Window", value=10, min_value=1)
long_window = st.sidebar.number_input("Long Moving Average Window", value=30, min_value=1)
trade_amount = st.sidebar.number_input("Trade Amount", value=0.001, min_value=0.0001, step=0.0001)
interval = st.sidebar.selectbox("Time Interval", ["1m", "5m", "15m", "1h", "1d"])
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", min_value=10, max_value=300, value=60)

# Initialize exchange
def init_exchange(name, api_key, api_secret):
    exchange_class = getattr(ccxt, name)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret,
    })
    return exchange

# Fetch market data
def fetch_data(exchange, symbol, interval):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=long_window)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Trading strategy
def trading_strategy(df, short_window, long_window):
    df['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1).mean()
    df['signal'] = 0
    df['signal'][short_window:] = np.where(df['short_mavg'][short_window:] > df['long_mavg'][short_window:], 1, 0)
    df['position'] = df['signal'].diff()
    return df

# Execute trade
def execute_trade(exchange, symbol, side, amount):
    order = exchange.create_order(symbol, 'market', side, amount)
    return order

# Main function
def main():
    if api_key and api_secret:
        exchange = init_exchange(exchange_name, api_key, api_secret)
        st.success(f"Connected to {exchange_name}")

        while True:
            data = fetch_data(exchange, symbol, interval)
            strategy_df = trading_strategy(data, short_window, long_window)

            # Display data and strategy signals
            st.subheader("Market Data")
            st.write(strategy_df.tail(10))

            st.subheader("Trading Signals")
            buy_signals = strategy_df[strategy_df['position'] == 1]
            sell_signals = strategy_df[strategy_df['position'] == -1]
            st.write("Buy Signals:")
            st.write(buy_signals)
            st.write("Sell Signals:")
            st.write(sell_signals)

            # Execute trades based on signals
            if not buy_signals.empty:
                execute_trade(exchange, symbol, 'buy', trade_amount)
                st.success("Executed Buy Order")

            if not sell_signals.empty:
                execute_trade(exchange, symbol, 'sell', trade_amount)
                st.success("Executed Sell Order")

            time.sleep(refresh_rate)
    else:
        st.error("Please enter your API key and secret")

if __name__ == "__main__":
    main()
