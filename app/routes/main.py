from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.get('/')
def index():
    return jsonify({
        "success": "Service is running!"
    }), 200