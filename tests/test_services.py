from sqlalchemy.exc import SQLAlchemyError
from app.services import MktDataSvc, TickerSvc
from app.models import Stock, TrackedTicker
from app.extensions import db
from unittest.mock import patch
import mock_data
import pytest

class TestMktDataSvc:

    def test_load_data_success(self, app):
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
    def test_load_data_handles_database_error(self, mock_rollback, mock_execute, app):
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

    def test_get_latest_data(self, app):
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

    def test_get_latest_data_returns_none(self, app):
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

    def test_get_historical_data(self, app):
        """
        Test that the service correctly fetches sorted historical data of
        given stock ticker
        """

        # Arrange: create multiple rows
        df = mock_data.get_mock_aapl_dataframe(single_row=False)
        mock_data.seed_stockdb_with_mock_data(df)

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

    def test_get_historical_data_returns_empty_list(self, app):
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
        assert len(returned_data) == 0

class TestTickerSvc:

    def test_add_new_ticker_success(self, app):
        """
        Test that a brand-new ticker is successfully added and returns True.
        """

        # Service execution
        result = TickerSvc.add("AAPL", auto_commit=True)

        # Assert service output
        assert result is True

        # Assert DB status
        saved_data = db.session.scalars(db.select(TrackedTicker)).all()
        assert len(saved_data) == 1
        assert saved_data[0].ticker == "AAPL"
        assert saved_data[0].is_active is True

    def test_add_duplicate_ticker_ignored(self, app):
        """
        Test that adding an existing ticker is ignored and returns False.
        """

        # Arrange: Pre-seed the database with AAPL
        TickerSvc.add("AAPL", auto_commit=True)

        # Service Execution - Add AAPL again.
        result = TickerSvc.add("AAPL", auto_commit=True)

        # Assert if the second attempt to add AAPL is ignored
        assert result is False

        # Assert DB status
        saved_data = db.session.scalars(db.select(TrackedTicker)).all()
        assert len(saved_data) == 1

    @patch('app.services.service.db.session.execute')
    @patch('app.services.service.db.session.rollback')
    def test_add_handles_database_error(self, mock_rollback, mock_execute, app):
        """
        Test that a DB failure triggers a rollback and raises a ValueError.
        """

        # Arrange
        mock_execute.side_effect = SQLAlchemyError("Simulated database crash!")

        # Service Execution
        with pytest.raises(ValueError, match="Failed to add ticker AAPL"):
            TickerSvc.add("AAPL", auto_commit=True)

        # Assertion
        mock_rollback.assert_called_once()
