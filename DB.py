from flask_login import *
from sqlalchemy import Column, ForeignKey, Integer, String,Binary,INT,Date,Table,LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

association_table =Table("who's_going_where", Base.metadata,
                    Column('user.id',Integer, ForeignKey('users.id')),
                    Column('events.id',Integer, ForeignKey('events.id'))
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


class Events(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    venue = Column(String(70), nullable=False)
    description = Column(String(2000), nullable=False)
    date = Column(String(15), nullable=False)
    time = Column(String(10),nullable=True)
    duration = Column(String(25),nullable=False)
    who_made_me = Column(String(25),nullable=False)
    address = Column(String(50),nullable=False)



class AUTH(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    password = Column(Binary(65), nullable=False)
    email = Column(String(30), nullable=False)
    phone_number = Column(String(15), nullable=True)
    community = Column(String(25), nullable=False)






engine = create_engine('sqlite:///users.db')


Base.metadata.create_all(engine)