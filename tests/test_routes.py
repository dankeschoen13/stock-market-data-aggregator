from unittest.mock import patch, MagicMock


@patch('app.routes.main.TickerSvc.get_active_tickers')
def test_get_available_tickers(mock_get_active_tickers, client):
    """
    Test if route correctly returns active tracked tickers using a mocked service layer.
    """

    # Create a fake object with a '.ticker' attribute
    mock_stock = MagicMock(ticker="AAPL")

    # Define the return value of the mock service
    mock_get_active_tickers.return_value = [mock_stock]

    # Call the API
    response = client.get('/api/tickers/active')

    # Assertions
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert "AAPL" in response.json["data"]
    assert response.json["meta"]["count"] == len(response.json["data"])

    # Strict assertion: Prove the route actually called the svc layer once
    mock_get_active_tickers.assert_called_once()