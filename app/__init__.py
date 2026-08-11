from flask import Flask, jsonify

from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, swagger, BLACKLISTED_TOKENS

# Import blueprints
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.chatbot import chatbot_bp
from app.routes.solar import solar_bp
from app.routes.weather import weather_bp
from app.routes.products import products_bp
from app.routes.crops import crops_bp
from app.routes.crop_guides import crop_guides_bp
from app.routes.diagnosis import diagnosis_bp
from app.routes.community import community_bp
from app.routes.tools import tools_bp
from app.routes.admin import admin_bp
from app.routes.ai import ai_bp
from app.routes.subscription import subscription_bp
from app.routes.marketplace import marketplace_bp
from app.routes.managed_crops import managed_crops_bp, public_catalogue_bp

def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # Configure CORS origins dynamically based on app config
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(cors_origins, str) and "," in cors_origins:
        cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    elif isinstance(cors_origins, str) and cors_origins != "*":
        cors_origins = [cors_origins.strip()]

    cors.init_app(
        app,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )
    swagger.init_app(app)

    # Import models for migrations
    from app import models as app_models  # noqa: F401

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(solar_bp, url_prefix="/api/solar")
    app.register_blueprint(weather_bp, url_prefix="/api/weather")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(crops_bp, url_prefix="/api/crops")
    app.register_blueprint(crop_guides_bp, url_prefix="/api/crop-guides")
    app.register_blueprint(diagnosis_bp, url_prefix="/api/diagnosis")
    app.register_blueprint(community_bp, url_prefix="/api/community")
    app.register_blueprint(tools_bp, url_prefix="/api/tools")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(subscription_bp, url_prefix="/api/subscription")
    app.register_blueprint(marketplace_bp, url_prefix="/api/marketplace")
    app.register_blueprint(managed_crops_bp, url_prefix="/api/admin/crops")
    app.register_blueprint(public_catalogue_bp, url_prefix="/api/catalogue/crops")

    # JWT token blacklist handling
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

    @app.route("/")
    def service_root():
        return jsonify({"success": True, "message": "Valam API is running", "health": "/api/health"}), 200

    @app.route("/api/health")
    def health_check():
        return jsonify({"success": True, "message": "API is running"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app
