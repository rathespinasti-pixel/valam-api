from flask import Flask, jsonify

from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, swagger, BLACKLISTED_TOKENS


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    swagger.init_app(app)

    # Import models so Flask-Migrate can detect them
    from app.models import user, chat, solar_guide, weather_subscription, product  # noqa: F401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.solar import solar_bp
    from app.routes.weather import weather_bp
    from app.routes.products import products_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(solar_bp, url_prefix="/api/solar")
    app.register_blueprint(weather_bp, url_prefix="/api/weather")
    app.register_blueprint(products_bp, url_prefix="/api/products")

    # JWT: check token blacklist (used for logout)
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLACKLISTED_TOKENS

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has been revoked"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "message": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "message": "Missing authorization token"}), 401

    # Health check
    @app.route("/api/health")
    def health_check():
        return jsonify({"success": True, "message": "API is running"}), 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app
