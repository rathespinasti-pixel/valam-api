import os
import sys
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app import create_app
from app.extensions import db

config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)


def init_db():
    """Verify the DB connection and create any missing tables."""
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        try:
            # Quick connectivity check before trying to create tables,
            # so a bad host/user/password/db-name gives a clear error
            # instead of a confusing stack trace.
            with db.engine.connect() as connection:
                pass
        except OperationalError as e:
            print("=" * 70)
            print("DATABASE CONNECTION FAILED")
            print(f"URI: {db_uri}")
            print(f"Error: {e}")
            print()
            print("Common fixes:")
            print("  1. Is MySQL running? (e.g. `sudo service mysql start`)")
            print("  2. Does the database exist? Run:")
            print("       CREATE DATABASE solar_farming_db CHARACTER SET utf8mb4;")
            print("  3. Check DATABASE_URL in your .env file matches your")
            print("     MySQL user/password/host/port/db name.")
            print("=" * 70)
            sys.exit(1)
        except SQLAlchemyError as e:
            print(f"Unexpected database error: {e}")
            sys.exit(1)

        # Import models so SQLAlchemy's metadata knows about every table
        # before create_all() runs (create_app already imports these, but
        # this keeps init_db safe to call standalone too).
        from app.models import user, chat, solar_guide, weather_subscription, product  # noqa: F401

        existing_tables = set(db.inspect(db.engine).get_table_names())
        db.create_all()
        new_tables = set(db.inspect(db.engine).get_table_names()) - existing_tables

        if new_tables:
            print(f"Created tables: {', '.join(sorted(new_tables))}")
        else:
            print("Database connected. All tables already exist.")


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
