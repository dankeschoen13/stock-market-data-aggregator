import requests
import pandas as pd
import os
from dotenv import load_dotenv



def fetch_historical_data(ticker, api_key):
    """
    Extracts raw JSON data from Financial Modeling Prep and converts it to a Pandas DataFrame.
    """

    url = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={ticker}&apikey={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        raw_json = response.json()

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

        dataframe = pd.DataFrame(daily_records)
        return dataframe

    elif response.status_code == 429:
        print("Rate limit exceeded! You hit the 250 calls/day limit.")
        return None
    else:
        print(f"API Error: {response.status_code} - {response.text}")
        return None


# --- Testing the Pipeline ---
load_dotenv()

if __name__ == "__main__":
    MY_API_KEY = os.environ.get('FMP_KEY')

    df = fetch_historical_data("AAPL", MY_API_KEY)

    if df is not None:
        print(df.head())