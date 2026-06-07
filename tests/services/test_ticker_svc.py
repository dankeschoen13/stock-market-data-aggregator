from sqlalchemy.exc import SQLAlchemyError
from app.services import TickerSvc
from app.models import TrackedTicker
from app.extensions import db
from unittest.mock import patch
import pytest

class TestAdd:

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

class TestSaveChanges:

    def test_save_changes_success(self, app):
        """
        Test that pending changes are successfully committed and returns True.
        """

        # Arrange
        TickerSvc.add("AAPL", auto_commit=False)

        # Service Execution
        success, error_message = TickerSvc.save_changes()

        # Assertions
        assert success is True
        assert error_message is None

        # Optional: Verify it actually made it to the database
        saved_data = db.session.scalars(db.select(TrackedTicker)).all()
        assert len(saved_data) == 1

    @patch('app.services.service.db.session.commit')  # Update path if needed!
    @patch('app.services.service.db.session.rollback')
    def test_save_changes_handles_error(self, mock_rollback, mock_commit, app):
        """
        Test that a database failure during commit triggers a rollback and returns False.
        """

        # Arrange
        TickerSvc.add("AAPL", auto_commit=False)
        mock_commit.side_effect = Exception("Simulated crash!")

        # Service Execution
        success, error_message = TickerSvc.save_changes()

        # Assertions
        assert success is False
        assert error_message == "Simulated crash!"
        mock_rollback.assert_called_once()


