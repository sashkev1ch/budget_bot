from sqlalchemy import Column, Integer, String, Identity
from library.database.models import Base


class Currencies(Base):
    __tablename__ = 'currencies'

    curr_id = Column(Integer, Identity(start=1), primary_key=True)
    currency_name = Column(String(150), nullable=False)
    currency_short_name = Column(String(3), nullable=False)
    currency_sign = Column(String(1), nullable=False)
