from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

class Database(db.Model):
    __tablename__ = 'users'
    pass