from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean, DateTime
from flask_login import UserMixin
from datetime import datetime

# Create Declarative Database
class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)

# ToDo: Create a User table for register
class User(UserMixin, db.Model):
  __tablename__ = "users"
  
  id:Mapped[int] = mapped_column(Integer, primary_key=True)
  username: Mapped[str] = mapped_column(String(80), unique=False, nullable=False)
  email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
  password_hash: Mapped[str] = mapped_column(String(250), nullable=False)
  confirmed_email: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[str] = mapped_column(DateTime, default=datetime.now)
  checks = relationship("Check", back_populates="user")


class Check(db.Model):
  __tablename__ = "checks"

  # One-to-Many relation between User and Check
  user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
  user = relationship("User", back_populates="checks")

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  module: Mapped[str] = mapped_column(Text, nullable=False)
  input_files: Mapped[str] = mapped_column(Text, nullable=False)
  output_files: Mapped[str] = mapped_column(Text, nullable=True)
  has_paid: Mapped[bool] = mapped_column(Boolean, default=False)
  result: Mapped[str] = mapped_column(Text, nullable=True)
  detail: Mapped[str] = mapped_column(Text, nullable=True)
  created_at: Mapped[str] = mapped_column(DateTime, default=datetime.now)