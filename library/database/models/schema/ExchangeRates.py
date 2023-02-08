from sqlalchemy import Column, Integer, String, Date, Identity, Numeric
from sqlalchemy.orm import relationship
from datetime import date
from library.database.models import Base


class ExchangeRates(Base):
    __tablename__ = 'exchange_rates'

    rate_id = Column(Integer, Identity(start=1), primary_key=True)
    currency_from = Column(String(5), nullable=False)
    currency_to = Column(String(5), nullable=False)
    ex_rate = Column(Numeric(precision=10, scale=2), nullable=False)
    rate_date = Column(Date, default=date.today())
