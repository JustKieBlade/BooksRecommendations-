from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, recommendations
from database import engine, get_db

# Создаем таблицы при старте
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Book Matcher AI Backend")


# НАСТРОЙКА CORS: Позволяет React (Vite), запущенному на любом порту, общаться с бэком
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для MVP разрешаем всё. На проде укажешь адрес фронта.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/favorites")
def add_to_favorites(user_id: int, book_id: int, db: Session = Depends(get_db)):
    # Находим книгу в общем пуле
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Книга не представлена в пуле")

    # Сохраняем КОПИЮ данных, чтобы они остались после очистки таблицы Book
    fav = models.Favorite(
        user_id=user_id,
        title=book.title,
        authors=book.authors,
        description=book.description,
        image_url=book.image_url,
        genres=book.genres
    )
    db.add(fav)
    db.commit()
    return {"status": "saved"}

@app.post("/api/users",
          response_model=schemas.ResponseModel if hasattr(schemas, 'ResponseModel') else schemas.UserResponse)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    tags_str = ", ".join(user_data.chosen_tags)
    db_user = models.User(chosen_tags=tags_str)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/api/books/next", response_model=schemas.BookResponse)
def get_next_book(user_id: int, db: Session = Depends(get_db)):
    book = recommendations.get_ai_recommendation(user_id, db)
    if not book:
        raise HTTPException(status_code=404, detail="Нет доступных книг для рекомендации")
    return book


@app.post("/api/books/action")
def user_action(action_data: schemas.ActionCreate, db: Session = Depends(get_db)):
    # Проверяем дубликат действия
    existing = db.query(models.UserAction).filter(
        models.UserAction.user_id == action_data.user_id,
        models.UserAction.book_id == action_data.book_id
    ).first()

    if existing:
        existing.action = action_data.action
    else:
        new_action = models.UserAction(
            user_id=action_data.user_id,
            book_id=action_data.book_id,
            action=action_data.action
        )
        db.add(new_action)

    db.commit()
    return {"status": "success", "message": f"Книга {action_data.action}нута успешно"}


@app.get("/api/favorites")
def get_favorites(user_id: int, db: Session = Depends(get_db)):
    # Возвращает все книги, скопированные в избранное для этого пользователя
    return db.query(models.Favorite).filter(models.Favorite.user_id == user_id).all()

@app.delete("/api/favorites/{fav_id}")
def delete_favorite(fav_id: int, db: Session = Depends(get_db)):
    # Удаляет книгу из таблицы избранного по её ID
    fav = db.query(models.Favorite).filter(models.Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Книга не найдена в избранном")
    db.delete(fav)
    db.commit()
    return {"status": "deleted", "message": "Книга удалена из избранного"}