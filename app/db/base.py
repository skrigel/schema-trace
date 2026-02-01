from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# This is required for Alembic autogenerate to detect models
from app.db import models  