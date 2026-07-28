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
            with db.engine.connect() as connection:
                pass
        except OperationalError as e:
            print("=" * 70)
            print("MYSQL CONNECTION FAILED - Falling back to local SQLite database...")
            print(f"Error: {e}")
            print("=" * 70)
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///valam_local.db"
            db.engine.dispose()

        # Import models so SQLAlchemy's metadata knows about every table
        # before create_all() runs (create_app already imports these, but
        # this keeps init_db safe to call standalone too).
        from app import models as app_models  # noqa: F401

        existing_tables = set(db.inspect(db.engine).get_table_names())
        db.create_all()
        new_tables = set(db.inspect(db.engine).get_table_names()) - existing_tables

        if new_tables:
            print(f"Created tables: {', '.join(sorted(new_tables))}")
        else:
            print("Database connected. All tables ready.")


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
