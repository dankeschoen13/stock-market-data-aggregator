from unittest.mock import patch, MagicMock


@patch('app.routes.main.TickerSvc.get_all')
def test_get_available_tickers(mock_svc, client):
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


@patch('app.routes.main.MktDataSvc.get_latest_data')
def test_get_latest_metrics(mock_svc, client):
    """
    Test if the route correctly fetches and serializes the latest stock row.
    """

    mock_stock_data = MagicMock()
    mock_stock_data.to_dict.return_value = {
        "ticker": "AAPL",
        "trade_date": "2026-06-03",
        "close": 150.00
    }

    mock_svc.return_value = mock_stock_data

    response = client.get('/api/data/AAPL/latest')

    # Assertions
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["data"]["ticker"] == "AAPL"
    assert response.json["data"]["close"] == 150.00

    # Strict assertion: Prove the route called the service layer with the right ticker
    mock_svc.assert_called_once_with("AAPL")
