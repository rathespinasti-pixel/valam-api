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

        # Ensure new columns exist on users, crops, and disease_diagnoses tables
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)

            if "users" in inspector.get_table_names():
                existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
                new_user_cols = [
                    ("farming_category", "VARCHAR(50) DEFAULT 'Farmer'"),
                    ("district", "VARCHAR(100) DEFAULT 'Vavuniya'"),
                    ("ds_division", "VARCHAR(100) DEFAULT 'Vavuniya Town'"),
                    ("gn_division", "VARCHAR(100)"),
                    ("land_size", "FLOAT DEFAULT 1.0"),
                    ("land_size_unit", "VARCHAR(20) DEFAULT 'Acres'"),
                    ("irrigation_preference", "VARCHAR(50) DEFAULT 'Drip Irrigation'"),
                    ("fertilizer_preference", "VARCHAR(50) DEFAULT 'Organic'"),
                    ("district_asc", "VARCHAR(100) DEFAULT 'Vavuniya Town'"),
                    ("farmer_type", "VARCHAR(50) DEFAULT 'Farmer'"),
                    ("farming_experience", "VARCHAR(50)"),
                    ("main_crops_grown", "VARCHAR(255)"),
                    ("preferred_language", "VARCHAR(10) DEFAULT 'en'"),
                    ("onboarding_completed", "BOOLEAN DEFAULT FALSE"),
                ]
                for col_name, col_def in new_user_cols:
                    if col_name not in existing_user_cols:
                        db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()

            if "crops" in inspector.get_table_names():
                existing_crop_cols = [c['name'] for c in inspector.get_columns('crops')]
                new_crop_cols = [
                    ("planting_method", "VARCHAR(50) DEFAULT 'Transplanting'"),
                    ("land_size", "FLOAT DEFAULT 0.5"),
                    ("land_size_unit", "VARCHAR(20) DEFAULT 'Acres'"),
                    ("irrigation_type", "VARCHAR(50) DEFAULT 'Drip Irrigation'"),
                    ("fertilizer_preference", "VARCHAR(50) DEFAULT 'Organic'"),
                ]
                for col_name, col_def in new_crop_cols:
                    if col_name not in existing_crop_cols:
                        db.session.execute(text(f"ALTER TABLE crops ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()

            if "disease_diagnoses" in inspector.get_table_names():
                existing_diag_cols = [c['name'] for c in inspector.get_columns('disease_diagnoses')]
                new_diag_cols = [
                    ("cause", "TEXT"),
                    ("organic_treatment", "TEXT"),
                    ("chemical_treatment", "TEXT"),
                    ("prevention_advice", "TEXT"),
                    ("language", "VARCHAR(10) DEFAULT 'en'"),
                ]
                for col_name, col_def in new_diag_cols:
                    if col_name not in existing_diag_cols:
                        db.session.execute(text(f"ALTER TABLE disease_diagnoses ADD COLUMN {col_name} {col_def}"))
                        db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Note on column migration: {e}")

        if new_tables:
            print(f"Created tables: {', '.join(sorted(new_tables))}")
        else:
            print("Database connected. All tables ready.")


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
