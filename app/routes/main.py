from flask import Blueprint, jsonify
from app.services import TickerSvc, MktDataSvc
from app.models import Stock

api_bp = Blueprint('api', __name__)

@api_bp.get('/')
def index():
    return jsonify({
        "success": "Service is running!"
    }), 200


@api_bp.get('/tickers/active')
def get_available_tickers():
    active_tickers = TickerSvc.get_active_tickers()

    if not active_tickers:
        return jsonify({
            "status": "error",
            "message": "No active tickers found in the database."
        }), 404

    return jsonify({
        "status": "success",
        "data": [stock.ticker for stock in active_tickers],
        "meta": {"count": len(active_tickers)},
    }), 200

@api_bp.get('/data/<str:ticker_symbol>/latest')
def get_latest_metric(ticker_symbol):

    latest_data = MktDataSvc.get_latest_data(ticker_symbol)
    
    if not latest_data:
        return jsonify({
            "status": "error",
            "message": f"No available data for ticker {ticker_symbol}",
        }), 404
    
    return jsonify({
        "status": "success",
        "data": latest_data.to_dict(),
    }), 200