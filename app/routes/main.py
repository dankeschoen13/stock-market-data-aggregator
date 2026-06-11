from flask import Blueprint, jsonify, request
from app.services import TickerSvc, MktDataSvc
from datetime import datetime
from app.models import Stock

api_bp = Blueprint('api', __name__)

@api_bp.get('/')
def index():
    return jsonify({
        "success": "Service is running!"
    }), 200


@api_bp.get('/tickers/active')
def get_available_tickers():
    active_tickers = TickerSvc.get_all()

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

@api_bp.get('/data/<string:ticker_symbol>/latest')
def get_latest_metrics(ticker_symbol):

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

@api_bp.get('/data/<string:ticker_symbol>/all')
def get_historical_data(ticker_symbol):

    start_date_str = request.args.get("start-date")
    end_date_str = request.args.get("end-date")

    start = None
    end = None

    # Parse strings to datetime.date objects (matching the service type hint)
    try:
        if start_date_str:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD."
        }), 400

    # Execute Service Layer, catching custom business logic errors
    try:
        historical_data = MktDataSvc.get_historical_data(
            ticker_symbol,
            start_date=start,
            end_date=end
        )

    except ValueError as e:
        # Catches the start_date > end_date time travel error
        return jsonify({"status": "error", "message": str(e)}), 400

    # Empty List handling
    if not historical_data:
        return jsonify({
            "status": "error",
            "message": f"No available data for ticker {ticker_symbol}",
        }), 404

    # Success handling
    return jsonify({
        "status": "success",
        "data": [stock.to_dict() for stock in historical_data],
        "meta": {"count": len(historical_data)},
    }), 200
