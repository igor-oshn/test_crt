import datetime

from typing import List, Optional
from pydantic import BaseModel


class RegisterUserRequest(BaseModel):
    name: str
    surname: str
    age: int


class UserModel(BaseModel):
    id: int
    name: str
    surname: str
    age: int

    class Config:
        orm_mode = True


class PicnicModel(BaseModel):
    city_id: int
    time: datetime.datetime

    class Config:
        orm_mode = True


class PicnicRegistrationResponseModel(BaseModel):
    id: int
    user: UserModel
    picnic: PicnicModel

    class Config:
        orm_mode = True


class PicnicRegistrationModel(BaseModel):
    user_id: int
    picnic_id: int

    class Config:
        orm_mode = True
