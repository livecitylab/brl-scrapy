# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper
# from sqlalchemy.engine.url import URL
import os
from dotenv import load_dotenv
load_dotenv()


Base = declarative_base()

# later, we create the engine
engine = create_engine(os.environ.get('DATABASE_URL'), pool_size=18, max_overflow=0)

# autoload rental table
metadata = MetaData(bind=engine)

class Rental(Base):
    __table__ = Table('rental', metadata, autoload=True)

# configure Session class with desired options
Session = sessionmaker()
# associate it with our custom Session class
Session.configure(bind=engine)
