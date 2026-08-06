import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared across environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME =  os.getenv("DB_NAME", "solar_farming_db")
    DB_PORT = os.getenv("DB_PORT", "3306")

    # Database
    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     "DATABASE_URL",
    #     "mysql+pymysql://root:password@localhost:3306/solar_farming_db",
    # )
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]

    # AI Chatbot provider
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
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

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
