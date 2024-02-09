import configparser
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import create_tables, add_default

settings = configparser.ConfigParser()
settings.read('setting.ini')
engine = sq.create_engine(settings['DEFAULT']['DSN'])

create_tables(engine)


Session = sessionmaker(bind=engine)
session = Session()

add_default(session)

session.commit()

