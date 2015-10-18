from aiopg.sa import AsyncMetaData
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base


metadata = AsyncMetaData()
Base = declarative_base(metadata=metadata)


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    agenda = Column(Text)
    social = Column(Text)
    url = Column(String(500))


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    text = Column(String(256))
