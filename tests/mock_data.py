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
        "trade_date": [datetime.date(2026, 6, 3), datetime.date(2026, 6, 2)],
        "close_price": [150.00, 148.50],
        "volume": [1250000, 1100000],
        "rsi_14": [55.5, 52.1]
    }

    df = pd.DataFrame(data)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    if single_row:
        df = df.iloc[[0]]

    return df