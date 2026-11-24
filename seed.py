import requests
from database import SessionLocal, engine
import models

API_KEY = "AIzaSyB8qfumn5CuxZngFc9jBCyBAx3YMmp4gic"
CATEGORIES = ["Fiction", "Fantasy", "Science", "History", "Mystery", "Biography", "Thriller", "Computers"]


def fetch_and_seed_books():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Проверяем, есть ли уже книги, чтобы не дублировать
    if db.query(models.Book).count() > 0:
        print("База данных уже наполнена книгами.")
        return

    print("Начинаем загрузку книг из Google Books...")

    for category in CATEGORIES:
        print(category)
        # Каждым запросом берем по 40 книг, смещаясь по index, чтобы набрать пул
        for start_index in range(0, 120, 40):
            url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{category}&maxResults=40&startIndex={start_index}&key={API_KEY}"
            try:
                response = requests.get(url).json()
                items = response.get("items", [])

                for item in items:
                    volume_info = item.get("volumeInfo", {})
                    google_id = item.get("id")

                    # Проверяем дубликаты по google_id
                    exists = db.query(models.Book).filter(models.Book.google_id == google_id).first()
                    if exists:
                        continue

                    title = volume_info.get("title", "Без названия")
                    authors = ", ".join(volume_info.get("authors", ["Неизвестный автор"]))
                    description = volume_info.get("description", "")
                    genres = ", ".join(volume_info.get("categories", [category]))

                    image_links = volume_info.get("imageLinks", {})
                    image_url = image_links.get("thumbnail") or image_links.get("smallThumbnail") or ""

                    # Пропускаем книги без описания (они бесполезны для ИИ)
                    if not description:
                        continue

                    book = models.Book(
                        google_id=google_id,
                        title=title,
                        authors=authors,
                        description=description,
                        image_url=image_url,
                        genres=genres
                    )
                    db.add(book)
                db.commit()
            except Exception as e:
                print(f"Ошибка при загрузке категории {category}: {e}")

    print(f"Готово! Всего книг в базе: {db.query(models.Book).count()}")
    db.close()


if __name__ == "__main__":
    fetch_and_seed_books()