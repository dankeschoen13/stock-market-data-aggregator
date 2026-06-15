from unittest.mock import patch, MagicMock
from datetime import  date

class TestGetAvailableTickers:
    """All tests related to the /api/tickers/active endpoint."""

    @patch('app.routes.main.TickerSvc.get_all')
    def test_success(self, mock_svc, client):
        """
        Test if route correctly returns active tracked tickers using a mocked service layer.
        """

        # Create a fake object with a '.ticker' attribute
        mock_ticker = MagicMock(ticker="AAPL")

        # Define the return value of mock `get_all` service
        mock_svc.return_value = [mock_ticker]

        # Call the API
        response = client.get('/api/tickers/active')

        # Assertions
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert "AAPL" in response.json["data"]
        assert response.json["meta"]["count"] == len(response.json["data"])

        # Strict assertion: Prove the route actually called the svc layer once
        mock_svc.assert_called_once()

    @patch('app.routes.main.TickerSvc.get_all')
    def test_error(self, mock_svc, client):
        """
        Test if the route correctly returns an error if there are no tracked tickers.
        """

        # Define the return value of mock `get_all` service
        mock_svc.return_value = []

        # Call the API
        response = client.get('/api/tickers/active')

        # Assertions
        assert response.status_code == 404
        assert response.json["status"] == "error"

        mock_svc.assert_called_once()

class TestGetLatestMetrics:
    """All tests related to the /api/tickers/<ticker>/latest endpoint."""

    @patch('app.routes.main.MktDataSvc.get_latest_data')
    def test_success(self, mock_svc, client):
        """
        Test if the route correctly fetches and serializes the latest stock row.
        """

        # Define the return value of mock `get_historical_data` service &
        # mock_stock_data to_dict property
        mock_stock_data = MagicMock()
        mock_stock_data.to_dict.return_value = {
            "ticker": "AAPL",
            "trade_date": "2026-06-03",
            "close": 150.00
        }

        mock_svc.return_value = mock_stock_data

        # API Call
        response = client.get('/api/data/AAPL/latest')

        # Assertions
        assert response.status_code == 200
        assert response.json["status"] == "success"
        assert response.json["data"]["ticker"] == "AAPL"
        assert response.json["data"]["close"] == 150.00

        # Strict assertion: Prove the route called the service layer with the right ticker
        mock_svc.assert_called_once_with("AAPL")

    @patch('app.routes.main.MktDataSvc.get_latest_data')
    def test_error(self, mock_svc, client):
        """
        Test if the route correctly returns an error for invalid stock tickers.
        """

        # Define the return value of mock `get_latest_data` service
        mock_svc.return_value = None

        # Call the API
        response = client.get('/api/data/INVALID/latest')

        # Assertions
        assert response.status_code == 404
        assert response.json["status"] == "error"

        mock_svc.assert_called_once_with("INVALID")

class TestGetHistoricalData:

    @patch('app.routes.main.MktDataSvc.get_historical_data')
    def test_success_no_time_window_returns_data(self, mock_svc, client):
        """
        Test if the route correctly fetches and serializes a list of market data for
        a given stock ticker
        """

        # Arrange
        mock_stock_data = MagicMock()
        mock_stock_data.to_dict.return_value = {
            "ticker": "AAPL",
            "trade_date": "2026-06-03",
            "close": 150.00
        }

        mock_svc.return_value = [mock_stock_data]

        # Call the API
        response = client.get('/api/data/AAPL/all')

        # Assertions
        assert response.status_code == 200
        assert response.json["status"] == "success"

        assert isinstance(response.json["data"], list)
        assert len(response.json["data"]) == 1
        assert response.json["meta"]["count"] == 1
        assert response.json["data"][0]["close"] == 150.00

        # Strict assertion: Prove the route called the service layer with the right ticker
        expected_start = None
        expected_end = None

        mock_svc.assert_called_once_with(
            "AAPL",
            start_date=expected_start,
            end_date=expected_end
        )

    @patch('app.routes.main.MktDataSvc.get_historical_data')
    def test_success_with_time_window_returns_data(self, mock_svc, client):
        """
        Test if the route correctly parses query string dates, fetches multiple
        rows, and serializes the market data.
        """

        # 1. Arrange: Create multiple mock objects with distinct to_dict returns
        mock_day_1 = MagicMock()
        mock_day_1.to_dict.return_value = {
            "ticker": "AAPL",
            "trade_date": "2026-06-03",
            "close": 150.00
        }

        mock_day_2 = MagicMock()
        mock_day_2.to_dict.return_value = {
            "ticker": "AAPL",
            "trade_date": "2026-06-02",
            "close": 148.50
        }

        # Return them as a list to simulate the SQLAlchemy scalars().all() return
        mock_svc.return_value = [mock_day_1, mock_day_2]

        # 2. Call the API using the query_string parameter
        response = client.get(
            '/api/data/AAPL/all',
            query_string={
                "start-date": "2026-06-01",
                "end-date": "2026-06-05"
            }
        )

        # 3. Assertions: Response State
        assert response.status_code == 200
        assert response.json["status"] == "success"

        # Assertions: Payload Data
        assert isinstance(response.json["data"], list)
        assert len(response.json["data"]) == 2
        assert response.json["meta"]["count"] == 2
        assert response.json["data"][0]["close"] == 150.00
        assert response.json["data"][1]["close"] == 148.50

        # 4. Strict Assertion: Prove the strings were parsed into date objects!
        expected_start = date(2026, 6, 1)
        expected_end = date(2026, 6, 5)

        mock_svc.assert_called_once_with(
            "AAPL",
            start_date=expected_start,
            end_date=expected_end
        )

    @patch('app.routes.main.MktDataSvc.get_historical_data')
    def test_invalid_ticker_returns_error(self, mock_svc, client):
        """
        Test if the route correctly catches a service-layer ValueError and returns a
        """

        # Define the return value of mock `get_historical_data` service
        mock_svc.return_value = []

        # Call the API
        response = client.get('/api/data/INVALID/all')

        # Assertions
        assert response.status_code == 404
        assert response.json["status"] == "error"

        # Strict assertion: Prove the route called the service layer with the right ticker
        mock_svc.assert_called_once_with(
            "INVALID",
            start_date=None,
            end_date=None
        )

    @patch('app.routes.main.MktDataSvc.get_historical_data')
    def test_invalid_date_format_returns_error(self, mock_svc, client):
        """
        Test if the route correctly returns a 400 error when an invalid date
        format is provided in the query string.
        """

        # Call the API
        response = client.get(
            '/api/data/AAPL/all',
            query_string={
                "start-date": "06-01-2026",
                "end-date": "2026-06-05"
            }
        )

        # Assertions
        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert response.json["message"] == "Invalid date format. Please use YYYY-MM-DD."

        mock_svc.assert_not_called()

    @patch('app.routes.main.MktDataSvc.get_historical_data')
    def test_start_date_after_end_date_returns_error(self, mock_svc, client):
        """
        Test if the route correctly catches a service-layer ValueError and
        returns a 400 error when the start date chronologically follows the end date.
        """

        # Arrange: Simulate the service layer rejecting the time-travel parameters
        mock_svc.side_effect = ValueError("Simulated service error!")

        # Call the API
        response = client.get(
            '/api/data/AAPL/all',
            query_string={
                "start-date": "2026-06-10",
                "end-date": "2026-06-05"
            }
        )

        # Assertions
        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert response.json["message"] == "Simulated service error!"

        # Strict Assertion: Prove the dates were still parsed correctly
        # before the service layer rejected them
        expected_start = date(2026, 6, 10)
        expected_end = date(2026, 6, 5)

        mock_svc.assert_called_once_with(
            "AAPL",
            start_date=expected_start,
            end_date=expected_end
        )

class TestGetTechnicallyOversold:

    @patch('app.routes.main.MktDataSvc.get_technically_oversold')
    def test_success_no_args_returns_data(self, mock_svc, client):
        """
        Test if the route correctly fetches and serializes a list of latest market data
        considered oversold based on the default rsi_threshold of 30.
        """

        # Arrange
        mock_stock_data = MagicMock()
        mock_stock_data.to_dict.return_value = {
            "ticker": "AAPL",
            "trade_date": "2026-06-14",
            "close": 150.00,
            "rsi_14": 30.00
        }
        mock_svc.return_value = [mock_stock_data]

        # Call the API
        response = client.get('/api/data/oversold')

        # Assertions
        assert response.status_code == 200
        assert response.json["status"] == "success"

        assert isinstance(response.json["data"], list)
        assert len(response.json["data"]) == 1
        assert response.json["meta"]["count"] == 1

        # Verify accurate JSON serialization
        assert response.json["data"][0]["close"] == 150.00
        assert response.json["data"][0]["rsi_14"] == 30
        assert response.json["data"][0]["trade_date"] == "2026-06-14"

        # Strict assertion: Prove the route called the service layer with correct defaults
        expected_trade_date = None
        expected_rsi = 30

        mock_svc.assert_called_once_with(
            trade_date=expected_trade_date,
            rsi_threshold=expected_rsi
        )

    @patch('app.routes.main.MktDataSvc.get_technically_oversold')
    def test_invalid_rsi_value_returns_error(self, mock_svc, client):
        """
        Test that the route returns a 400 Bad Request when a non-integer
        string is provided for the RSI threshold, successfully blocking service execution.
        """

        # Call the API
        response = client.get(
            '/api/data/oversold',
            query_string={"rsi": "one-hundred"}
        )

        # Assertions
        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert response.json["message"] == "Invalid RSI value. Please choose an integer between 0 and 100."

        mock_svc.assert_not_called()

    @patch('app.routes.main.MktDataSvc.get_technically_oversold')
    def test_invalid_date_format_returns_error(self, mock_svc, client):
        """
        Test that the route returns a 400 Bad Request when an incorrectly formatted
        date string is provided, successfully blocking service execution.
        """

        # Call the API
        response = client.get(
            '/api/data/oversold',
            query_string={"trade-date": "06-01-2026"}
        )

        # Assertions
        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert response.json["message"] == "Invalid date format. Please use YYYY-MM-DD."

        mock_svc.assert_not_called()

    @patch('app.routes.main.MktDataSvc.get_technically_oversold')
    def test_service_validation_returns_error(self, mock_svc, client):
        """
        Test that the route correctly catches a service-layer ValueError and
        returns a 400 Bad Request when business logic validation fails
        (e.g., RSI parameter is out of bounds).
        """
        mock_svc.side_effect = ValueError("Simulated service error!")

        # Call the API
        response = client.get(
            '/api/data/oversold',
            query_string={
                "rsi": "105",
                "trade-date": "2026-06-05"
            }
        )

        # Assertions
        assert response.status_code == 400
        assert response.json["status"] == "error"
        assert response.json["message"] == "Simulated service error!"

        # Strict Assertion
        expected_rsi = 105
        expected_trade_date = date(2026, 6, 5)

        mock_svc.assert_called_once_with(
            trade_date=expected_trade_date,
            rsi_threshold=expected_rsi
        )

    @patch('app.routes.main.MktDataSvc.get_technically_oversold')
    def test_no_matching_data_returns_error(self, mock_svc, client):
        """
        Test that the route correctly catches a service-layer ValueError and
        returns a 400 Bad Request when business logic validation fails
        (e.g., RSI parameter is out of bounds).
        """
        # Arrange
        mock_svc.return_value = []
        expected_date = date.today()

        # Call the API
        response = client.get('/api/data/oversold')

        # Assertions
        assert response.status_code == 404
        assert response.json["status"] == "error"
        assert response.json["message"] == f"No oversold stocks found for {expected_date}."

        # Strict Assertion
        expected_rsi = 30

        mock_svc.assert_called_once_with(
            trade_date=None,
            rsi_threshold=expected_rsi
        )