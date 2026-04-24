from sqlalchemy import Column, Integer, String, DateTime
from database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    password = Column(String)

    gender = Column(String, default="Prefer not to say")
    region = Column(String, default="Unknown")

    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)

    profile_image = Column(String, nullable=True)