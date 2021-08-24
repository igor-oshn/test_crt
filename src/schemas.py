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


class CityModel(BaseModel):
    name: str

    class Config:
        orm_mode = True

class CityModelResponse(BaseModel):
    id: int
    name: str
    weather: float

    class Config:
        orm_mode = True


class PicnicModel(BaseModel):
    city_id: int
    time: datetime.datetime

    class Config:
        orm_mode = True


class PicnicModelResponse(BaseModel):
    id: int
    city: str
    time: datetime.datetime
    users: Optional[List[UserModel]]

    class Config:
        orm_mode = True


class PicnicRegistrationModel(BaseModel):
    user_id: int
    picnic_id: int

    class Config:
        orm_mode = True


class PicnicRegistrationModelResponse(BaseModel):
    id: int
    user: UserModel
    picnic: PicnicModel

    class Config:
        orm_mode = True
