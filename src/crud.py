from sqlalchemy.orm import Session

import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.RegisterUserRequest):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_city(db: Session, city_id: int):
    return db.query(models.City).filter(models.City.id == city_id).first()


def create_city(db: Session, city: str):
    db_city = models.City(name=city.capitalize())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


def get_picnic(db: Session, picnic_id: int):
    return db.query(models.Picnic).filter(models.Picnic.id == picnic_id).first()


def create_picnic(db: Session, picnic: schemas.PicnicRegistrationModel):
    db_picnic = models.Picnic(**picnic.dict())
    db.add(db_picnic)
    db.commit()
    db.refresh(db_picnic)
    return db_picnic


def get_picnic_register(db: Session, picnic_id: int):
    return db.query(models.PicnicRegistration).filter(models.PicnicRegistration.id == picnic_id).first()


def create_picnic_register(db: Session, pic_reg: schemas.PicnicRegistrationModel):
    db_pic_reg = models.PicnicRegistration(**pic_reg.dict())
    db.add(db_pic_reg)
    db.commit()
    db.refresh(db_pic_reg)
    return db_pic_reg


def check_unique_pic_reg(db: Session, user: int, picnic: int):
    if db.query(models.PicnicRegistration).filter(models.PicnicRegistration.user_id == user,
                                                  models.PicnicRegistration.picnic_id == picnic).first():
        return False
    return True
