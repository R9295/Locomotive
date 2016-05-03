from flask_login import *
from sqlalchemy import Column, ForeignKey, Integer, String,Binary,INT,Date,Table,LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import DateTime
import datetime
Base = declarative_base()

association_table =Table("who's_going_where", Base.metadata,
                    Column('user.id',Integer, ForeignKey('users.id')),
                    Column('events.id',Integer, ForeignKey('events.id'))
                    )


association_table_for_past =Table("who_went_where", Base.metadata,
                    Column('user.id',Integer, ForeignKey('users.id')),
                    Column('past_events.id',Integer, ForeignKey('past_events.id'))
                    )


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    password = Column(Binary(65), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    community = Column(String(25), nullable=False)
    going_to = relationship("Events",
                            secondary = association_table,
                            backref="who_is_coming"
                            )
    went_to = relationship("Past_Events",
                           secondary= association_table_for_past,
                           backref="who_came"

    )


class Events(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    venue = Column(String(70), nullable=False)
    description = Column(String(2000), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String(10),nullable=True)
    duration = Column(String(25),nullable=False)
    who_made_me = Column(String(25),nullable=False)
    address = Column(String(50),nullable=False)
    image = Column(String(40),nullable=True)
    when_made = Column(DateTime,nullable=False)
  #  type_of = Column(String(40),nullable=False)


class AUTH(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    password = Column(Binary(65), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    community = Column(String(25), nullable=False)


class Past_Events(Base):
    __tablename__ = 'past_events'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    venue = Column(String(70), nullable=False)
    description = Column(String(2000), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String(10),nullable=True)
    duration = Column(String(25),nullable=False)
    who_made_me = Column(String(25),nullable=False)
    address = Column(String(50),nullable=False)
    image = Column(String(40),nullable=True)



engine = create_engine('sqlite:///users.db',connect_args={'check_same_thread':False},poolclass=StaticPool)


Base.metadata.create_all(engine)