import pandas as pd
import datetime

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