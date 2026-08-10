from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    status = Column(String, default='processing') # processing|awaiting_input|open|calculated|cancelled
    receipt_type = Column(String) # highlighted|plain
    image_url = Column(String)
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    service_charge = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    payer_user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    calculated_at = Column(DateTime)
    
    items = relationship("Item", back_populates="session", cascade="all, delete")
    participants = relationship("Participant", back_populates="session", cascade="all, delete")
    votes = relationship("Vote", back_populates="session", cascade="all, delete")


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    line_total = Column(Float, default=0.0)
    highlight_color = Column(String) # nullable
    is_shared = Column(Boolean, default=False)
    
    session = relationship("Session", back_populates="items")


class Participant(Base):
    __tablename__ = 'participants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    telegram_user_id = Column(String, nullable=False)
    display_name = Column(String)
    highlight_color = Column(String) # nullable

    session = relationship("Session", back_populates="participants")


class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    telegram_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="votes")
