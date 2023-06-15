from sqlalchemy import Column, Integer, String, DateTime, Identity
from sqlalchemy.orm import relationship
from datetime import datetime
from library.database.models import Base


class Users(Base):
    __tablename__ = 'bot_users'

    tg_id = Column(Integer, Identity(start=1), primary_key=True)
    user_name = Column(String(150), nullable=False, unique=True)
    user_full_name = Column(String(250), nullable=True)
    create_date = Column(DateTime, default=datetime.now())
    admin_yn = Column(String(1), default='N')
    balance = relationship("Balances", back_populates="user")
