from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
from datetime import datetime
import models
import schemas
import crud
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Middleware
@app.middleware("http")
async def db_session_middleware(request, call_next):
    response = await call_next(request)
    return response

# Upload file endpoint
@app.post("/files/", response_model=schemas.File)
def create_file(file: UploadFile = File(...), comment: str = "", db: Session = Depends(get_db)):
    file_path = os.path.join("./uploaded_files", file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Получаем размер файла с помощью os.path.getsize
    file_size = os.path.getsize(file_path)

    file_data = {
        "name": file.filename.rsplit('.', 1)[0],
        "extension": '.' + file.filename.rsplit('.', 1)[1],
        "size": file_size,
        "path": file_path,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "comment": comment
    }

    # Преобразование словаря в Pydantic модель
    file_create = schemas.FileCreate(**file_data)

    return crud.create_file(db=db, file=file_create)

# List files endpoint
@app.get("/files/", response_model=list[schemas.File])
def list_files(db: Session = Depends(get_db)):
    return crud.get_files(db)

# Get file info endpoint
@app.get("/files/{file_id}", response_model=schemas.File)
def get_file_info(file_id: int, db: Session = Depends(get_db)):
    file_info = crud.get_file(db, file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File info not found in database")
    return file_info

# Update file info endpoint
@app.patch("/files/{file_id}", response_model=schemas.File)
def update_file(file_id: int, file_update: schemas.FileUpdate, db: Session = Depends(get_db)):
    db_file = crud.get_file(db, file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Проверяем и обновляем данные файла
    if file_update.name:
        # Удаляем символы "/" из названия файла
        new_name = file_update.name.replace("/", "")

        # Если после удаления "/" название стало пустым, выдаем ошибку
        if not new_name:
            raise HTTPException(status_code=400, detail="File name cannot be empty or contain '/'")

        db_file.name = new_name

    if file_update.path:
        new_path = file_update.path

        # Проверяем безопасность пути
        if not is_safe_path(new_path):
            raise HTTPException(status_code=400, detail="Unsafe file path")

        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        new_full_path = os.path.join(new_path, f"{db_file.name}{db_file.extension}")
        os.rename(db_file.path, new_full_path)
        db_file.path = new_full_path

    if file_update.comment is not None:
        db_file.comment = file_update.comment

    db_file.updated_at = datetime.utcnow()

    # Сохраняем обновленный файл в базе данных
    db.commit()
    db.refresh(db_file)

    return db_file

def is_safe_path(path: str) -> bool:
    """
    Проверяет, является ли путь безопасным для сохранения файлов в директории 'uploaded_files'.
    """
    base_path = os.path.abspath("./uploaded_files")
    requested_path = os.path.abspath(path)

    return os.path.commonpath([base_path]) == os.path.commonpath([base_path, requested_path])

# Delete file endpoint
@app.delete("/files/{file_id}", response_model=dict)
def delete_file(file_id: int, db: Session = Depends(get_db)):
    file_info = crud.get_file(db, file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_info.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    crud.delete_file(db, file_id)

    return {"detail": "File deleted"}

