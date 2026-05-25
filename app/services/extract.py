import requests
import pandas as pd
import os
from dotenv import load_dotenv

def fetch_latest_stock_data(ticker, api_key) -> pd.DataFrame | None:
    """
    Extracts raw JSON data from Financial Modeling Prep and converts it to a Pandas DataFrame.

    Args:
        ticker: A valid US stock ticker
        api_key: FMP-issued API key for the endpoint.
    Returns:
        pd.Dataframe: Stock historical data with added MACD and RSI columns
    """

    url = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={ticker}&apikey={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        raw_json = response.json()

        # 1. Handle data based on the returned format
        if isinstance(raw_json, dict):
            daily_records = raw_json.get('historical', [])

        elif isinstance(raw_json, list):
            daily_records = raw_json

        else:
            print(f"Unexpected JSON structure: {type(raw_json)}")
            daily_records = []

        if not daily_records:
            print(f"No historical data found for {ticker}.")
            return None

        # 2. Prepare the dataframe and ensure it's always sorted in ascending order
        df = pd.DataFrame(daily_records)

        df['date'] = pd.to_datetime(df['date'])
        df.sort_values('date', ascending=True).reset_index(drop=True)

        # 3. Add MACD and RSI columns to the dataframe
        df = add_macd(df)
        df = add_rsi(df)

        # 4. Rename columns to match the current database
        df = df.rename(columns={
            'date': 'trade_date',
            'open': 'open_price',
            'close': 'close_price',
            'high': 'high_price',
            'low': 'low_price'
        })

        # 5. Return the completed dataframe
        df = df.tail(1)

        return df

    elif response.status_code == 429:
        print("Rate limit exceeded! You hit the 250 calls/day limit.")
        return None
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return None


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Moving Average Convergence Divergence (MACD) and appends it to the DataFrame.

    Computational Logic:
    - MACD Line: The difference between the 12-period and 26-period Exponential Moving Averages (EMA).
    - Signal Line: A 9-period EMA of the MACD Line.
    - Histogram: The difference between the MACD Line and the Signal Line.

    Args:
        df (pd.DataFrame): DataFrame containing a 'close' column.

    Returns:
        pd.DataFrame: The original DataFrame with 'macd_line', 'macd_signal', and 'macd_histogram' columns added.
    """
    # 12-period and 26-period EMAs
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()

    # MACD Line: Fast EMA - Slow EMA
    df['macd_line'] = ema_12 - ema_26

    # Signal Line: 9-period EMA of the MACD Line
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()

    # Histogram: MACD Line - Signal Line
    df['macd_histogram'] = df['macd_line'] - df['macd_signal']

    return df


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Relative Strength Index (RSI) and appends it to the DataFrame.

    Computational Logic:
    - RSI measures the speed and change of price movements on a scale of 0 to 100.
    - It uses a 14-period lookback, isolating gains and losses.
    - RS (Relative Strength) = Average Gain / Average Loss.
    - RSI = 100 - (100 / (1 + RS)).
    - Uses J. Welles Wilder's original smoothing method (alpha = 1/14).

    Args:
        df (pd.DataFrame): DataFrame containing a 'close' column.

    Returns:
        pd.DataFrame: The original DataFrame with an 'rsi' column added.
    """
    # Day-to-day price differences
    delta = df['close'].diff()

    # Isolate positive and negative price changes (losses converted to positive values)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 14-period smoothed moving average (Wilder's smoothing)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()

    # Relative Strength (RS)
    rs = avg_gain / avg_loss

    # RSI Formula
    df['rsi'] = 100 - (100 / (1 + rs))

    return df


# --- Testing the Pipeline ---
load_dotenv()

if __name__ == "__main__":
    MY_API_KEY = os.environ.get('FMP_KEY')

    dataframe = fetch_historical_data("AAPL", MY_API_KEY)

    if dataframe is not None:
        print(dataframe.tail(10))