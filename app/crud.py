from sqlalchemy.orm import Session
import models
import schemas


def get_file(db: Session, file_id: int):
    return db.query(models.File).filter(models.File.id == file_id).first()


def get_file_by_name(db: Session, name: str):
    return db.query(models.File).filter(models.File.name == name).first()


def get_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.File).offset(skip).limit(limit).all()


def create_file(db: Session, file: schemas.FileCreate):
    file_dict = file.dict()
    db_file = models.File(**file_dict)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def update_file(db: Session, file_id: int, file_data: schemas.FileUpdate):
    db_file = get_file(db, file_id)
    if db_file:
        update_data = file_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_file, key, value)
        db.commit()
        db.refresh(db_file)
        return db_file
    return None


def delete_file(db: Session, name: str):
    db_file = get_file_by_name(db, name)
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False
