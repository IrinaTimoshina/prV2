import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models

# Создаем тестовую базу данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Переопределяем зависимость get_db для использования тестовой базы данных
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_file():
    file_path = "test_file.txt"
    with open(file_path, "w") as f:
        f.write("This is a test file")

    with open(file_path, "rb") as f:
        response = client.post("/files/", files={"file": ("test_file.txt", f)}, data={"comment": "Test file comment"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_file"
    assert data["extension"] == ".txt"
    assert data["comment"] == "Test file comment"

    os.remove(file_path)


def test_list_files():
    response = client.get("/files/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_file_info():
    response = client.get("/files/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "test_file"


def test_update_file():
    response = client.patch("/files/1", json={"name": "updated_file_name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_file_name"


def test_delete_file():
    response = client.delete("/files/1")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "File deleted"

    response = client.get("/files/1")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "File info not found in database"
