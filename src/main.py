import datetime as dt
import logging
import random
import string
import time
from typing import List
from urllib.request import Request

from fastapi import FastAPI, HTTPException, Query, Depends
from database import engine, Session, Base
from models import City, User, Picnic, PicnicRegistration
from external_requests import GetWeatherRequest
from pydantic.types import conint
from schemas import CityModel, CityModelResponse, RegisterUserRequest, UserModel, PicnicRegistrationModel, PicnicModel,\
                    PicnicModelResponse, PicnicRegistrationModelResponse
import crud

Base.metadata.create_all(bind=engine)

# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project.
                                      # This will get the root logger since no logger in the configuration has this name.

app = FastAPI()


# Dependency
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.post('/cities/', summary='Create City', description='Создание города по его названию', tags=['cities'],
          response_model=CityModelResponse)
def create_city(city: CityModel, db: Session = Depends(get_db)):
    check = GetWeatherRequest()
    if not check.check_existing(city.name):
        raise HTTPException(status_code=400, detail='Параметр city должен быть существующим городом')

    city_object = db.query(City).filter(City.name == city.name.capitalize()).first()
    if city_object is None:
        city_object = crud.create_city(db, city.name)
    return {'id': city_object.id, 'name': city_object.name, 'weather': city_object.weather}


@app.get('/cities/', summary='Get Cities', description='Получение списка городов',
         tags=['cities'], response_model=List[CityModelResponse])
def cities_list(q: str = Query(description="Название города", default=None), db: Session = Depends(get_db)):
    """
    Получение списка городов

    Фильтры:
    - поиск по названию города
    """
    if q:
        cities = db.query(City).filter(City.name.contains(q))
    else:
        cities = db.query(City).all()

    return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city in cities]


@app.get('/users/', summary='Get Users', tags=['users'], description='Получение списка пользователей',
         response_model=List[UserModel])
def users_list(min_age: conint(ge=0, le=120) = Query(default=None, description='Минимальный возраст', ),
               max_age: conint(ge=0, le=120) = Query(default=None, description='Максимальный возраст'),
               db: Session = Depends(get_db)):
    """
    Список пользователей

    Фильтры:
    - мин./макс. возраст
    """
    users = db.query(User)
    if min_age:
        users = users.filter(User.age >= min_age)
    if max_age:
        users = users.filter(User.age <= max_age)
    return [{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'age': user.age,
    } for user in users]


@app.post('/users/', summary='Create User', tags=['users'], description='Создание пользователя',
          response_model=UserModel)
def register_user(user: RegisterUserRequest, db: Session = Depends(get_db)):
    """
    Регистрация пользователя
    """
    user_obj = crud.create_user(db, user)
    return {
        'id': user_obj.id,
        'name': user_obj.name,
        'surname': user_obj.surname,
        'age': user_obj.age,
    }


@app.get('/picnics/', summary='Get Picnics', tags=['picnics'], description='Получение списка пикников',
         response_model=List[PicnicModelResponse])
def picnics_list(datetime: dt.datetime = Query(default=None, description='Время пикника (по умолчанию не задано)'),
                 past: bool = Query(default=True, description='Включая уже прошедшие пикники'),
                 db: Session = Depends(get_db)):
    """
    Список всех пикников
    """
    picnics = db.query(Picnic)
    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        print(dt.datetime.now())
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())
    return [{
        'id': pic.id,
        'city': pic.city.name,
        'time': pic.time,
        'users': [
            {
                'id': pr.user.id,
                'name': pr.user.name,
                'surname': pr.user.surname,
                'age': pr.user.age,
            }
            for pr in db.query(PicnicRegistration).filter(PicnicRegistration.picnic_id == pic.id)],
    } for pic in picnics]


@app.post('/picnics/', summary='Create Picnic', tags=['picnics'], description='Создание пикника',
          response_model=PicnicModelResponse)
def create_picnic(pic: PicnicModel, db: Session = Depends(get_db)):
    """
    Добавление пикника
    """
    if not crud.get_city(db, pic.city_id):
        raise HTTPException(status_code=400, detail=f'Город id:{pic.city_id} не найден')
    p = crud.create_picnic(db, pic)

    return {
        'id': p.id,
        'city': p.city.name,
        'time': p.time,
        'user': p.users
    }


@app.post('/picnic-register/', summary='Create Picnic Registration', tags=['picnic-register'],
          description='Регистрация пользователя на пикник',
          response_model=PicnicRegistrationModelResponse)
def picnic_register(pic_reg: PicnicRegistrationModel, db: Session = Depends(get_db)):
    """
    Регистрация пользователя на пикник
    """

    if not crud.check_unique_pic_reg(db, pic_reg.user_id, pic_reg.picnic_id):
        raise HTTPException(status_code=400, detail=f'Пользователь id:{pic_reg.user_id} уже добавлен на пикник')

    if not crud.get_user(db, pic_reg.user_id):
        raise HTTPException(status_code=400, detail=f'Пользователь id:{pic_reg.user_id} не найден')

    if not crud.get_picnic(db, pic_reg.picnic_id):
        raise HTTPException(status_code=400, detail=f'Пикник id:{pic_reg.picnic_id} не найден')

    pr = crud.create_picnic_register(db, pic_reg)

    return {
        'id': pr.id,
        'picnic': pr.picnic,
        'user': pr.user,
    }
