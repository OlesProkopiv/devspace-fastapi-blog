from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("Запускаємо автоматичний скрапінг...")

# Відкриваємо браузер
driver = webdriver.Chrome()

try:
    # 1. Відкриваємо головну сторінку сайту
    driver.get("http://127.0.0.1:8000/")
    time.sleep(1)  # Даємо сторінці секунду на базове завантаження

    # 2. Клікаємо на "Увійти" в меню навігації
    print("Відкриваємо форму входу...")
    nav_login_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "nav-login"))
    )
    nav_login_btn.click()

    # 3. Авторизація
    print("Проходимо авторизацію...")
    # Чекаємо, поки поле логіна стане видимим (анімація SPA)
    username_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "login-username"))
    )
    password_input = driver.find_element(By.ID, "login-password")

    # Кнопку шукаємо за атрибутом onclick, бо в неї немає id
    login_button = driver.find_element(By.XPATH, "//button[@onclick='login()']")

    # Вводимо дані
    username_input.send_keys("Oles")
    password_input.send_keys("qwer1234")
    login_button.click()

    # 4. Чекаємо успішного входу (наприклад, поки з'явиться кнопка "Вийти")
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "nav-logout"))
    )
    print("Авторизація успішна!")

    # 5. Переходимо на Головну сторінку, щоб зчитати пости
    nav_home_btn = driver.find_element(By.XPATH, "//button[text()='Головна']")
    nav_home_btn.click()

    # Даємо скрипту 2 секунди, щоб JS встиг стягнути пости з БД і відмалювати їх
    time.sleep(2)

    # 6. Зчитуємо дані постів
    print("Зчитуємо пости...")
    # Збираємо всі елементи з класом "post"
    posts = driver.find_elements(By.CLASS_NAME, "post")

    print(f"\n--- ЗНАЙДЕНО ПОСТІВ: {len(posts)} ---")
    for index, post in enumerate(posts, start=1):
        # Зчитуємо текст поста (перший рядок зазвичай заголовок)
        post_title = post.text.splitlines()[0] if post.text else "Без заголовка"
        print(f"Пост #{index}: {post_title}")

    print("---------------------------------")
    print("Скрапінг успішно завершено!")

finally:
    # Залишаємо браузер відкритим на 3 секунди, щоб ти міг побачити результат
    time.sleep(3)
    driver.quit()