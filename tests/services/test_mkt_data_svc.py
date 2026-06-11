from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta
from app.services import MktDataSvc
from app.models import Stock
from app.extensions import db
from unittest.mock import patch
import pandas as pd
import mock_data
import pytest

class TestLoadData:

    def test_success(self, app):
        """
        Test that the service correctly loads the given pandas df to database.
        """

        # Arrange
        df = mock_data.get_mock_aapl_dataframe(single_row=True)

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

    @patch('app.services.service.db.session.execute')
    @patch('app.services.service.db.session.rollback')
    def test_handles_database_error(self, mock_rollback, mock_execute, app):
        """
        Test that a DB failure triggers a rollback and raises a ValueError.
        """

        # Arrange: Get mock data and set mock_execute's side effect
        df = mock_data.get_mock_aapl_dataframe(single_row=True)
        mock_execute.side_effect = SQLAlchemyError("Simulated database crash")

        # Service execution and assertion: Catch the expected custom error
        with pytest.raises(ValueError, match="Failed to load data for AAPL"):
            MktDataSvc.load_data(df)

        # Verify the side effects
        mock_rollback.assert_called_once()

class TestGetLatestData:

    def test_success_returns_stock_obj(self, app):
        """
        Test that the service correctly fetches and sorts the most recent date.
        """

        # Arrange: create multiple rows
        df = mock_data.get_mock_aapl_dataframe(single_row=False)
        mock_data.seed_stockdb_with_mock_data(df)

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

    def test_returns_none(self, app):
        """
        Test that the service correctly returns None when a non-existent
        ticker_symbol is passed in.
        """

        # Arrange data
        df = mock_data.get_mock_aapl_dataframe(single_row=True)
        MktDataSvc.load_data(df)

        # Service Execution
        returned_data = MktDataSvc.get_latest_data("MSFT")

        # Assertions
        assert returned_data is None

class TestGetHistoricalData:

    def test_success_default_window_returns_list_of_stock_objects(self, app):
        """
        Test that the service correctly fetches sorted historical data of
        given stock ticker using the default 30-day lookback window.
        """

        # Arrange
        df = mock_data.get_mock_aapl_dataframe(single_row=False)
        start_date = pd.to_datetime(date.today() - timedelta(days=30))
        df_within_30_days = df.loc[df["trade_date"] >= start_date]

        mock_data.seed_stockdb_with_mock_data(df)

        # Service Execution
        returned_data = MktDataSvc.get_historical_data("AAPL")

        # Assertions
        assert isinstance(returned_data, list)
        assert len(returned_data) == len(df_within_30_days)

        sorted_df = df_within_30_days.sort_values(
            by="trade_date",
            ascending=False,
            ignore_index=True
        )

        for i in range(len(returned_data)):
            # Extract the pure Python date from the Pandas Timestamp!
            expected_date = sorted_df.iloc[i]["trade_date"].date()

            assert returned_data[i].trade_date == expected_date
            assert returned_data[i].close_price == sorted_df.iloc[i]["close_price"]

    def test_success_with_specified_window_returns_list_of_stock_objects(self, app):
        """
        Test that the service correctly fetches sorted historical data strictly
        bounded by the explicitly provided start_date and end_date.
        """

        # Arrange: Create dataframe
        df = mock_data.get_mock_aapl_dataframe(single_row=False)

        # Define start and end dates
        start_date = date.today() - timedelta(days=29)
        end_date = date.today() - timedelta(days=5)

        # Seed Data
        mock_data.seed_stockdb_with_mock_data(df)

        # Set index and slice df to match expected returned data
        df_within_window = df.loc[
            (df["trade_date"] >= pd.to_datetime(start_date)) &
            (df["trade_date"] <= pd.to_datetime(end_date))
            ]

        # Service Execution
        returned_data = MktDataSvc.get_historical_data(
            ticker_symbol="AAPL",
            start_date=start_date,
            end_date=end_date
        )

        # Assertions
        assert isinstance(returned_data, list)
        assert len(returned_data) == len(df_within_window)

        sorted_df = df_within_window.sort_values(
            by="trade_date",
            ascending=False,
            ignore_index=True
        )

        for i in range(len(returned_data)):
            # Extract the pure Python date from the Pandas Timestamp!
            expected_date = sorted_df.iloc[i]["trade_date"].date()

            assert returned_data[i].trade_date == expected_date
            assert returned_data[i].close_price == sorted_df.iloc[i]["close_price"]

    def test_default_window_returns_empty_list(self, app):
        """
        Test that the service correctly returns an empty list when a non-existent
        ticker_symbol is passed in.
        """

        # Arrange data
        df = mock_data.get_mock_aapl_dataframe(single_row=False)
        mock_data.seed_stockdb_with_mock_data(df)

        # Service Execution
        returned_data = MktDataSvc.get_historical_data("MSFT")

        # Assertions
        assert isinstance(returned_data, list)
        assert len(returned_data) == 0


class TestGetTechnicallyOversold:
    """Unit tests for the MktDataSvc.get_technically_oversold method."""

    def test_success_default_date_and_rsi_returns_list_of_stock_obj(self, app):
        """
        Test that the method correctly fetches a list of Stock objects
        matching the default RSI threshold (<= 30) for the current date.
        """
        # Arrange
        df = mock_data.get_mock_aapl_dataframe(single_row=False)
        mock_data.seed_stockdb_with_mock_data(df)

        today_timestamp = pd.to_datetime(date.today())
        expected_df = df.loc[
            (df["trade_date"] == today_timestamp) &
            (df["rsi_14"] <= 30)
            ]
        expected_count = len(expected_df)

        # Service Execution
        returned_data = MktDataSvc.get_technically_oversold()

        # Assertions
        assert isinstance(returned_data, list)
        assert len(returned_data) == expected_count

        for i in range(len(returned_data)):
            assert returned_data[i].rsi_14 <= 30
            assert returned_data[i].trade_date == date.today()

    def test_returns_empty_list_for_unmatched_criteria(self, app):
        """
        Test that the method correctly returns an empty list when no market
        data matches the requested trade date or RSI threshold.
        """
        # Arrange
        df = mock_data.get_mock_aapl_dataframe(single_row=True)
        mock_data.seed_stockdb_with_mock_data(df)

        requested_date = date(2026, 1, 1)

        target_timestamp = pd.to_datetime(requested_date)
        expected_df = df.loc[
            (df["trade_date"] == target_timestamp) &
            (df["rsi_14"] <= 30)
            ]
        expected_count = len(expected_df)

        # Service Execution
        returned_data = MktDataSvc.get_technically_oversold(trade_date=requested_date)

        # Assertions
        assert isinstance(returned_data, list)
        assert len(returned_data) == expected_count
        assert len(returned_data) == 0 
