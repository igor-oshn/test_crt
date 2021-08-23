import datetime as dt
from fastapi import FastAPI, HTTPException, Query, Depends
from database import engine, Session, Base
from models import City, User, Picnic, PicnicRegistration
from external_requests import CheckCityExisting, GetWeatherRequest
from pydantic.types import conint
from schemas import RegisterUserRequest, UserModel, PicnicRegistrationModel, PicnicModel
import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@app.post('/cities/', summary='Create City', description='Создание города по его названию')
def create_city(city: str = Query(..., description="Название города"), db: Session = Depends(get_db)):
    check = CheckCityExisting()
    if not check.check_existing(city):
        raise HTTPException(status_code=400, detail='Параметр city должен быть существующим городом')

    city_object = db.query(City).filter(City.name == city.capitalize()).first()
    if city_object is None:
        city_object = City(name=city.capitalize())
        s = Session()
        s.add(city_object)
        s.commit()

    return {'id': city_object.id, 'name': city_object.name, 'weather': city_object.weather}


@app.get('/cities/', summary='Get Cities')
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


@app.get('/users/', summary='Get Users')
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


@app.post('/users/', summary='Create User', response_model=UserModel)
def register_user(user: RegisterUserRequest, db: Session = Depends(get_db)):
    """
    Регистрация пользователя
    """
    user_obj = crud.create_user(db, user)
    return user_obj


@app.get('/picnics/', summary='Get Picnics', tags=['picnic'])
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


@app.post('/picnics/', summary='Create Picnic', tags=['picnic'])
def picnic_add(pic: PicnicModel, db: Session = Depends(get_db)):
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
    }


@app.post('/picnic-register/', summary='Create Picnic Registration', tags=['picnic'])
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
        'picnic': pr.picnic.id,
        'user': pr.user.name,
    }
