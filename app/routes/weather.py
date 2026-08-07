from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.weather_subscription import WeatherSubscription
from app.utils.decorators import success_response, error_response, get_current_user
from app.utils.weather_client import get_current_weather, get_forecast, get_alerts
from app.utils.advisory import generate_agro_advisory

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/advisory", methods=["GET"])
def weather_advisory():
    """
    Get weather-based agricultural advisory for a location.
    Query params: ?location=Vavuniya,LK
    ---
    tags: [Weather]
    """
    location = request.args.get("location", "Vavuniya,LK")
    current = get_current_weather(location)
    forecast_data = get_forecast(location, days=5)
    advisories = generate_agro_advisory(location, current, forecast_data)

    return success_response({
        "location": location,
        "current": current,
        "forecast": forecast_data,
        "advisories": advisories,
    })



@weather_bp.route("/current", methods=["GET"])
def current_weather():
    """
    Get current weather for a location.
    Query params: ?location=City,CountryCode
    ---
    tags: [Weather]
    """
    location = request.args.get("location")
    if not location:
        return error_response("location query parameter is required", 400)

    data = get_current_weather(location)
    return success_response(data)


@weather_bp.route("/forecast", methods=["GET"])
def forecast():
    """
    Get 7-day weather forecast for a location.
    Query params: ?location=City,CountryCode&days=7
    ---
    tags: [Weather]
    """
    location = request.args.get("location")
    if not location:
        return error_response("location query parameter is required", 400)

    days = request.args.get("days", 7, type=int)
    data = get_forecast(location, days)
    return success_response(data)


@weather_bp.route("/alerts", methods=["GET"])
def alerts():
    """
    Get active weather alerts for a location.
    Query params: ?location=City,CountryCode
    ---
    tags: [Weather]
    """
    location = request.args.get("location")
    if not location:
        return error_response("location query parameter is required", 400)

    data = get_alerts(location)
    return success_response(data)


@weather_bp.route("/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    """
    Subscribe the logged-in user to weather alerts for a location.
    ---
    tags: [Weather]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    location = data.get("location")
    if not location:
        return error_response("location is required", 400)

    sub = WeatherSubscription(
        user_id=user.id,
        location=location,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        alert_types=data.get("alert_types", "all"),
    )
    db.session.add(sub)
    db.session.commit()

    return success_response(sub.to_dict(), message="Subscribed to weather alerts", status_code=201)
