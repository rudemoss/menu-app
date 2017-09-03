import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class UserID(Base):
    __tablename__ = 'user_id'
    
    id = Column(
        Integer, primary_key = True
    ) 
    name = Column(
        String(80), nullable = False
    )
    email = Column(
        String(80), nullable = False
    )
    picture = Column(
        String(150), nullable = False
    )

    @property
    def serialize(self):
        return {
            'name'  : self.name,
            'id'    : self.id,
            'email' : self.email,
            'picture': self.picture
        }
          


class Restaurant(Base):
    __tablename__ = 'restaurant'

    name = Column(
        String(80), nullable = False
    )
    id = Column(
        Integer, primary_key = True
    )

    user_id = Column(
        Integer, ForeignKey('user_id.id')
    )
    user_id = relationship(UserID)

    @property
    def serialize(self):
        return {
            'name'  : self.name,
            'id'    : self.id
        }


class MenuItem(Base):
    __tablename__ = 'menu_item'

    name = Column(
        String(80), nullable = False
    )
    id = Column(
        Integer, primary_key = True
    )
    course = Column(
        String(250)
    )
    description = Column(
        String(250)
    )
    price = Column(
        String(250)
    )
    restaurant_id = Column(
        Integer, ForeignKey('restaurant.id')
    )
    restaurant = relationship(Restaurant)
    
    user_id = Column(
        Integer, ForeignKey('user_id.id')
    )

    @property
    def serialize(self):
        return {
            'name'          : self.name,
            'id'            : self.id,
            'description'   : self.description,
            'price'         : self.price,
            'course'        : self.course
        }

engine = create_engine(
    'sqlite:///restaurantmenu.db')

Base.metadata.create_all(engine)
