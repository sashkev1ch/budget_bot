from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, Identity, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from library.database.models import Base


class BalanceHistory(Base):
    __tablename__ = 'balance_history'

    bhist_id = Column(Integer, Identity(start=1), primary_key=True)
    blnc_blnc_id = Column(Integer, ForeignKey("balances.blnc_id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), default=0.00)
    update_value = Column(Numeric(precision=10, scale=2), default=0.00)
    curr_curr_id = Column(Integer, ForeignKey("currencies.curr_id"), nullable=False)
    change_date = Column(DateTime, default=datetime.now())
    balance = relationship("Balances", back_populates="balance_history")
