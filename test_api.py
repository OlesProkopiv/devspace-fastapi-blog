import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db
import models

# 1. Використовуємо фізичний файл замість пам'яті
TEST_DB_URL = "sqlite:///./test_app.db"

# 2. Очищуємо стару тестову БД перед запуском тестів (якщо вона є)
if os.path.exists("./test_app.db"):
    os.remove("./test_app.db")

# 3. Налаштовуємо підключення
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Створюємо таблиці в тестовій базі
models.Base.metadata.create_all(bind=engine)

# 5. Підміняємо залежність, щоб FastAPI використовував тестову базу
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- ТЕСТИ ---

def test_register_user():
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@test.com", "password": "password123"}
    )
    # Зміни 200 на 201
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@test.com"

def test_login_user():
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_post():
    # Отримуємо токен
    login_response = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Створюємо пост
    post_response = client.post(
        "/posts/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Тестовий пост", "content": "Це текст для тесту"}
    )
    # Зміни 200 на 201
    assert post_response.status_code == 201
    assert post_response.json()["title"] == "Тестовий пост"

def test_read_posts():
    response = client.get("/posts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)