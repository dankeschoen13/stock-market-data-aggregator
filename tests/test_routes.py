from app.services import TickerSvc

def test_get_available_tickers(client):
    """
    Test if route correctly returns active tracked tickers in the database
    """

    # DB Injection
    TickerSvc.add_new_ticker(ticker_symbol="AAPL", auto_commit=True)

    # API Call
    response = client.get('/api/tickers/active')

    # Assertions
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert "AAPL" in response.json["data"]
    assert response.json["meta"]["count"] == len(response.json["data"])