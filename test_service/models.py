import asyncio
from aiopg.sa import AsyncMetaData
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from aiopg.sa import create_engine
from test_service.settings import DATABASE_HOST, DATABASE_PASSWORD,\
    DATABASE_NAME, DATABASE_USERNAME


metadata = AsyncMetaData()
Base = declarative_base(metadata=metadata)


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    text = Column(String(256))


@asyncio.coroutine
def setup(app):
    engine = yield from create_engine(user=DATABASE_USERNAME,
                                      database=DATABASE_NAME,
                                      host=DATABASE_HOST,
                                      password=DATABASE_PASSWORD)
    app['db_engine'] = engine
    app['db_declarative_base'] = Base
    metadata.bind = engine
