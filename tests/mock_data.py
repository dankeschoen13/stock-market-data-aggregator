from app.services import MktDataSvc,TickerSvc
from datetime import date, timedelta
import pandas as pd

def seed_stockdb_with_mock_data(df: pd.DataFrame):
    """
    Iterates through a DataFrame and loads rows sequentially into the database
    to bypass the single-row limitation of the load_data service.
    """

    for i in range(len(df)):
        MktDataSvc.load_data(df.iloc[[i]])

def seed_stockdb_with_mock_tickers(tickers: list):
    """
    Iterates through a list of tickers and sequentially adds them into the db
    """
    for ticker in tickers:
        TickerSvc.add(ticker, auto_commit=False)

    TickerSvc.save_changes()

def get_mock_aapl_dataframe(single_row: bool = True) -> pd.DataFrame:
    """
    Returns a mocked DataFrame matching the output of the extraction layer.
    """
    today = date.today()

    data = {
        "ticker": "AAPL",
        "trade_date": [
            today,  # Day 0: The exact upper boundary
            today - timedelta(days=5),  # Day 5: Safely inside the window
            today - timedelta(days=29), # Day 29: The exact lower boundary
            today - timedelta(days=30), # Day 30: The edge-case (depending on >= or > logic)
            today - timedelta(days=31), # Day 31: OUTSIDE the window (Should be filtered out)
            today - timedelta(days=45)  # Day 45: Safely outside the window
        ],
        "close_price": [150.00, 148.50, 145.90, 142.10, 138.50, 135.00],
        "volume": [1250000, 1100000, 1020000, 890000, 950000, 800000],
        "rsi_14": [28.5, 52.1, 43.5, 38.2, 35.0, 22.1]
    }

    df = pd.DataFrame(data)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    if single_row:
        df = df.iloc[[0]]

    return df