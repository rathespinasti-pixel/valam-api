import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


class Config:
    """Base configuration shared across environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Accept both the app's local names and Railway's MySQL plugin names.
    DB_USER = os.getenv("DB_USER") or os.getenv("MYSQLUSER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQLHOST", "localhost")
    DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE", "solar_farming_db")
    DB_PORT = os.getenv("DB_PORT") or os.getenv("MYSQLPORT", "3306")

    # Railway commonly supplies DATABASE_URL or MYSQL_URL. Normalize legacy
    # schemes so SQLAlchemy selects a driver installed by this project.
    _database_url = (os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL") or "").strip()
    if _database_url.startswith("mysql://"):
        _database_url = _database_url.replace("mysql://", "mysql+pymysql://", 1)
    elif _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _database_url or (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", 7))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # AI Chatbot provider & Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GWMINI_API_KEY", "")
    # gemini-1.5-flash/-pro have been retired ("no longer available to new
    # users") - gemini-flash-latest is the current text model alias.
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    # Image generation requires a dedicated image-capable model - text models
    # can never return image bytes, regardless of prompt.
    GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    AI_PROVIDER_API_KEY = os.getenv("AI_PROVIDER_API_KEY", "")
    AI_PROVIDER_URL = os.getenv(
        "AI_PROVIDER_URL", "https://api.anthropic.com/v1/messages"
    )

    # Weather provider
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_BASE_URL = os.getenv(
        "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5"
    )

    # Perenual API provider
    PERENUAL_API_KEY = os.getenv("PERENUAL_API_KEY") or os.getenv("PRENUAL_API_KEY", "")
    PERENUAL_BASE_URL = os.getenv("PERENUAL_BASE_URL", "https://perenual.com/api")

    # CORS
    _raw_cors = os.getenv("CORS_ORIGINS", "*")
    _vercel_origin = r"https://.*\.vercel\.app"
    if _raw_cors == "*":
        CORS_ORIGINS = "*"
    elif "," in _raw_cors:
        CORS_ORIGINS = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]
        CORS_ORIGINS.append(_vercel_origin)
    else:
        CORS_ORIGINS = (
            [_raw_cors.strip(), _vercel_origin] if _raw_cors.strip() else "*"
        )

    # Swagger
    SWAGGER = {
        "title": "Solar Farming Assistant API",
        "uiversion": 3,
        "specs_route": "/api/docs/",
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
