from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional
import models, schemas, database

# Створюємо таблиці в БД
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Blog API with Auth")

# налаштування безпеки
SECRET_KEY = "super_secret_key_for_lab3"  # Секретний ключ для підпису токенів
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Функція, яка перевіряє токен у кожному захищеному запиті
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# роздача фронтенду (HTML/CSS/JS)

# підключу папку "static" пізніше
import os

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    # Головна сторінка буде віддавати наш HTML
    return FileResponse("static/index.html")


# авторизація та USERS API

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Перевіряємо чи є такий юзер
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Хешуємо пароль перед збереженням
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    # Повертає дані про поточного залогіненого юзера
    return current_user


@app.get("/users/me/posts/", response_model=List[schemas.Post])
def read_my_posts(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    # Повертає пости лише поточного залогіненого юзера (від нових до старих)
    return db.query(models.Post).filter(models.Post.owner_id == current_user.id).order_by(
        models.Post.created_at.desc()).all()


# POSTS CRUD (Захищені маршрути)

@app.post("/posts/", response_model=schemas.Post, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostBase, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(get_current_user)):
    # Зверни увагу: owner_id тепер береться автоматично з current_user!
    db_post = models.Post(title=post.title, content=post.content, owner_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/", response_model=List[schemas.Post])
def read_posts(
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "newest",
        search: Optional[str] = None,  # Додано параметр пошуку
        db: Session = Depends(database.get_db)
):
    query = db.query(models.Post)

    # Фільтрація за заголовком (пошук)
    if search:
        query = query.filter(models.Post.title.contains(search))

    if sort_by == "newest":
        query = query.order_by(models.Post.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(models.Post.created_at.asc())
    elif sort_by == "title":
        query = query.order_by(models.Post.title.asc())

    return query.offset(skip).limit(limit).all()


@app.put("/posts/{post_id}", response_model=schemas.Post)
def update_post(
        post_id: int,
        post_update: schemas.PostUpdate,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # Реалізація методу PUT для CRUD
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_post.title = post_update.title
    db_post.content = post_update.content
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(get_current_user)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    # Перевірка, чи видаляє юзер саме свій пост
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(post)
    db.commit()
    return


# COMMENTS CRUD

@app.post("/comments/", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
def create_comment(comment: schemas.CommentCreate, db: Session = Depends(database.get_db),
                   current_user: models.User = Depends(get_current_user)):
    # Створюємо коментар, прив'язуючи його до поста і до поточного користувача
    db_comment = models.Comment(text=comment.text, post_id=comment.post_id, owner_id=current_user.id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment