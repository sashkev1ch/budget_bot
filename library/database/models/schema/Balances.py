from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, Identity, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from library.database.models import Base


class Balances(Base):
    __tablename__ = 'balances'

    blnc_id = Column(Integer, Identity(start=1), primary_key=True)
    tg_tg_id = Column(Integer, ForeignKey("bot_users.tg_id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), default=0.00)
    curr_curr_id = Column(Integer, ForeignKey("currencies.curr_id"), nullable=False)
    create_date = Column(DateTime, default=datetime.now())
    change_date = Column(DateTime, default=datetime.now())
    user = relationship("Users", back_populates="balance")
