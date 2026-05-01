from locust import HttpUser, task, between
import random
import string


class BlogLoadTest(HttpUser):
    # Віртуальні юзери будуть робити паузу від 1 до 3 секунд між діями
    wait_time = between(1, 3)

    def on_start(self):
        """
        Цей метод виконується один раз для кожного віртуального юзера під час запуску.
        Ми генеруємо унікального користувача, реєструємо його та отримуємо токен.
        """
        # Генеруємо випадковий логін, щоб уникнути помилок унікальності в БД
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        self.username = f"user_{random_str}"
        self.password = "supersecret123"

        # 1. Реєстрація
        self.client.post("/users/", json={
            "username": self.username,
            "email": f"{self.username}@test.com",
            "password": self.password
        })

        # 2. Логін (отримуємо токен - перша частина складного сценарію)
        response = self.client.post("/login", data={
            "username": self.username,
            "password": self.password
        })

        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(2)
    def get_all_posts(self):
        """Проста дія: читання стрічки постів (виконується вдвічі частіше)"""
        self.client.get("/posts/")

    @task(1)
    def create_new_post(self):
        """
        Складна дія: створення поста.
        Використовує токен, отриманий на етапі логіну (друга частина складного сценарію).
        """
        if self.token:
            self.client.post(
                "/posts/",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "title": f"Пост від {self.username}",
                    "content": "Locust тестує навантаження системи!"
                }
            )