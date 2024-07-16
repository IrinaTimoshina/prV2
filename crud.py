from sqlalchemy.orm import Session
from . import models, schemas

def create_file(db: Session, file: dict) -> models.File:
    db_file = models.File(**file)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_files(db: Session) -> list[models.File]:
    return db.query(models.File).all()

def get_file(db: Session, file_id: int) -> models.File:
    return db.query(models.File).filter(models.File.id == file_id).first()

def get_file_by_name(db: Session, file_name: str) -> models.File:
    return db.query(models.File).filter(models.File.name == file_name).first()

def update_file(db: Session, file_id: int, file_update: dict) -> models.File:
    db_file = get_file(db, file_id)
    if db_file:
        for key, value in file_update.items():
            setattr(db_file, key, value)
        db.commit()
        db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int):
    db_file = get_file(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
