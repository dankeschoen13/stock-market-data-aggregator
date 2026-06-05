from mock_data import get_mock_aapl_dataframe
from app.services import MktDataSvc
from app.models import Stock
from app.extensions import db

class TestMktDataSvc:

    def test_load_data(self, app):

        # Arrange
        df = get_mock_aapl_dataframe(single_row=True)

        # Service Execution
        MktDataSvc.load_data(df)

        # Assertions
        saved_data = db.session.scalars(
            db.select(Stock).where(Stock.ticker == "AAPL")
        ).all()
        assert len(saved_data) == 1
        assert saved_data is not None

        first_record = saved_data[0]
        assert first_record.ticker == "AAPL"
        assert first_record.close_price == df["close_price"].iloc[0]
        assert first_record.rsi_14 == df["rsi_14"].iloc[0]

    def test_get_latest_data(self, app):
        """
        Test that the service correctly fetches and sorts the most recent date.
        """

        # Arrange: create multiple rows
        df = get_mock_aapl_dataframe(single_row=False)

        for i in range(len(df)):
            single_row_df = df.iloc[[i]]
            MktDataSvc.load_data(single_row_df)

        # Service Execution
        returned_data = MktDataSvc.get_latest_data("AAPL")

        # Assertions against dataframe
        assert returned_data is not None
        assert returned_data.ticker == "AAPL"

        # Prove that it grabbed latest data
        sorted_df = df.sort_values(
            by="trade_date",
            ascending=False,
            ignore_index=True
        )
        assert returned_data.close_price == sorted_df["close_price"].iloc[0]
        assert returned_data.rsi_14 == sorted_df["rsi_14"].iloc[0]

    def test_get_historical_data(self, app):
        """
        Test that the service correctly fetches sorted historical data of
        given stock ticker
        """

        # Arrange: create multiple rows
        df = get_mock_aapl_dataframe(single_row=False)
        for i in range(len(df)):
            single_row_df = df.iloc[[i]]
            MktDataSvc.load_data(single_row_df)

        # Service Execution
        returned_data = MktDataSvc.get_historical_data("AAPL")

        # Assertions
        assert returned_data is not None
        assert len(returned_data) == len(df)

        sorted_df = df.sort_values(
            by="trade_date",
            ascending=False,
            ignore_index=True
        )
        assert returned_data[0].close_price == sorted_df["close_price"].iloc[0]
        assert returned_data[1].close_price == sorted_df["close_price"].iloc[1]

    