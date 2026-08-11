import sys
from app import create_app
from app.extensions import db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('crops')]
    if 'latitude' not in columns:
        db.session.execute(text('ALTER TABLE crops ADD COLUMN latitude FLOAT NULL'))
        print('Added latitude column')
    if 'longitude' not in columns:
        db.session.execute(text('ALTER TABLE crops ADD COLUMN longitude FLOAT NULL'))
        print('Added longitude column')
    db.session.commit()
    print('Migration complete')
