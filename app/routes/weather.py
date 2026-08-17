from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.weather_controller import (
    weather_advisory,
    current_weather,
    forecast,
    alerts,
    subscribe,
)

weather_bp = Blueprint("weather", __name__)

weather_bp.add_url_rule("/advisory", view_func=weather_advisory, methods=["GET"])
weather_bp.add_url_rule("/current", view_func=current_weather, methods=["GET"])
weather_bp.add_url_rule("/forecast", view_func=forecast, methods=["GET"])
weather_bp.add_url_rule("/alerts", view_func=alerts, methods=["GET"])
weather_bp.add_url_rule("/subscribe", view_func=jwt_required()(subscribe), methods=["POST"])
