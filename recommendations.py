import random
import numpy as np  # <-- ДОБАВИЛИ ИМПОРТ NUMPY
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
import models


def get_ai_recommendation(user_id: int, db: Session):
    # 1. Получаем все действия пользователя
    actions = db.query(models.UserAction).filter(models.UserAction.user_id == user_id).all()
    liked_book_ids = [a.book_id for a in actions if a.action == 'like']
    disliked_book_ids = [a.book_id for a in actions if a.action == 'dislike']

    # Все книги, с которыми пользователь уже взаимодействовал
    seen_book_ids = liked_book_ids + disliked_book_ids

    # Если пользователь еще ничего не лайкнул, выдаем случайную книгу на основе его стартовых тегов
    if not liked_book_ids:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user and user.chosen_tags:
            tags = [t.strip().lower() for t in user.chosen_tags.split(",")]
            query_books = db.query(models.Book).all()
            matching_books = [
                b for b in query_books
                if any(tag in (b.genres or "").lower() for tag in tags) and b.id not in seen_book_ids
            ]
            if matching_books:
                return random.choice(matching_books)

        available_books = db.query(models.Book).filter(~models.Book.id.in_(seen_book_ids)).all()
        return random.choice(available_books) if available_books else None

    # 2. ИИ-подбор (TF-IDF + Cosine Similarity)
    all_books = db.query(models.Book).all()
    if not all_books:
        return None

    # Формируем тексты для анализа
    corpus = [f"{b.genres or ''} {b.description or ''}" for b in all_books]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Индексы лайкнутых книг в общем списке
    book_id_to_index = {book.id: idx for idx, book in enumerate(all_books)}
    liked_indices = [book_id_to_index[bid] for bid in liked_book_ids if bid in book_id_to_index]

    if not liked_indices:
        available_books = db.query(models.Book).filter(~models.Book.id.in_(seen_book_ids)).all()
        return random.choice(available_books) if available_books else None

    # Строим вектор профиля пользователя как среднее векторов лайкнутых книг
    user_profile_vector = tfidf_matrix[liked_indices].mean(axis=0)

    # Конвертируем устаревший np.matrix в стандартный numpy array
    user_profile_vector = np.asarray(user_profile_vector)

    # Считаем схожесть этого профиля со ВСЕМИ книгами
    similarity_scores = cosine_similarity(user_profile_vector, tfidf_matrix).flatten()

    # Сортируем книги по схожесть (от большей к меньшей)
    ranked_indices = similarity_scores.argsort()[::-1]

    # Ищем первую книгу, которую пользователь еще не видел
    for idx in ranked_indices:
        candidate_book = all_books[idx]
        if candidate_book.id not in seen_book_ids:
            # С вероятностью 20% даем шанс другой книге из Топ-5 лучших для разнообразия пула
            top_candidates = []
            for check_idx in ranked_indices:
                b = all_books[check_idx]
                if b.id not in seen_book_ids:
                    top_candidates.append(b)
                if len(top_candidates) >= 5:
                    break

            if top_candidates and random.random() < 0.2:
                return random.choice(top_candidates)

            return candidate_book

    return None