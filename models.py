from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String)  # Сохраняем как строку через запятую
    description = Column(Text)
    image_url = Column(String)
    genres = Column(String)  # Сохраняем теги/жанры как строку через запятую

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    chosen_tags = Column(String)  # Стартовые теги через запятую

class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    action = Column(String, nullable=False)  # 'like' или 'dislike'

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String)
    authors = Column(String)
    description = Column(Text)
    image_url = Column(String)
    genres = Column(String)