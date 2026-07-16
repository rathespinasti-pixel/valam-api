from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
swagger = Swagger()

# In-memory blacklist for revoked JWT tokens (logout).
# For production/multi-instance deployments, swap this for a Redis set.
BLACKLISTED_TOKENS = set()
