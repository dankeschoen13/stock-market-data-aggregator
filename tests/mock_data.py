from app.services import MktDataSvc,TickerSvc
import pandas as pd
import datetime

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
    data = {
        "ticker": "AAPL",
        "trade_date": [
            datetime.date(2026, 6, 3),
            datetime.date(2026, 6, 2),
            datetime.date(2026, 6, 1),
            datetime.date(2026, 5, 29), # Friday
            datetime.date(2026, 5, 28),
            datetime.date(2026, 5, 27),
            datetime.date(2026, 5, 15), # Mid-window test
            datetime.date(2026, 5, 1)   # Out-of-bounds test for the 30-day default
        ],
        "close_price": [150.00, 148.50, 149.20, 147.80, 146.50, 145.90, 142.10, 138.50],
        "volume": [1250000, 1100000, 1150000, 980000, 1050000, 1020000, 890000, 950000],
        "rsi_14": [55.5, 52.1, 53.8, 49.2, 45.1, 43.5, 38.2, 35.0]
    }

    df = pd.DataFrame(data)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    if single_row:
        df = df.iloc[[0]]

    return df