from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=False, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    full_name = Column(String(120), nullable=True)
    created_at = Column(String(50), nullable=False)
    