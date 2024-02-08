import configparser
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import create_tables

settings = configparser.ConfigParser()
settings.read('setting.ini')
engine = sq.create_engine(settings['DEFAULT']['DSN'])

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()


session.commit()

