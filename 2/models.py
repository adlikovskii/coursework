import json
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Default(Base):
    __tablename__ = "default"

    id = sq.Column(sq.Integer, primary_key=True)
    eng = sq.Column(sq.String(length=40), nullable=False)
    rus = sq.Column(sq.String(length=40), nullable=False)


class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    cid = sq.Column(sq.BigInteger, unique=True, nullable=False)


class Status(Base):
    __tablename__ = "status"

    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    w1 = sq.Column(sq.Boolean, nullable=False)
    w2 = sq.Column(sq.Boolean, nullable=False)
    w3 = sq.Column(sq.Boolean, nullable=False)
    w4 = sq.Column(sq.Boolean, nullable=False)
    w5 = sq.Column(sq.Boolean, nullable=False)
    w6 = sq.Column(sq.Boolean, nullable=False)
    w7 = sq.Column(sq.Boolean, nullable=False)
    w8 = sq.Column(sq.Boolean, nullable=False)
    w9 = sq.Column(sq.Boolean, nullable=False)
    w10 = sq.Column(sq.Boolean, nullable=False)

    user = relationship(User, backref="s_user")


class Personal(Base):
    __tablename__ = "personal"

    id = sq.Column(sq.Integer, primary_key=True)
    eng = sq.Column(sq.String(length=40), nullable=False)
    rus = sq.Column(sq.String(length=40), nullable=False)
    id_user = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)

    user = relationship(User, backref="p_user")


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def add_default(session):
    with open('default/default.json') as fd:
        data = json.load(fd)

    for record in data:
        model = {
            'default': Default,
        }[record.get('model')]
        session.add(model(id=record.get('pk'), **record.get('fields')))
    session.commit()


def add_default_status(session, id_user):
    with open('default/status.json') as fd:
        data = json.load(fd)

    for record in data:
        model = {
            'status': Status,
        }[record.get('model')]
        session.add(model(id_user=id_user, **record.get('fields')))
    session.commit()
