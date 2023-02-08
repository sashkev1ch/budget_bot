from datetime import datetime, date
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from library.database.models import Base
from library.database.models.schema import *
import decimal

class DbAdapter:
    def __init__(self, host, user, password, database):
        self._host = host
        self._user = user
        self._password = password
        self._database = database

        self._engine = create_engine(
            f"postgresql+psycopg2://"
            f"{self._user}:"
            f"{self._password}@{self._host}:"
            f"5432/{self._database}",
            echo=False
        )

    def get_session(self):
        session = sessionmaker()
        return session(bind=self._engine)

    def init_db(self, admin_id, admin_name):
        Base.metadata.create_all(self._engine)
        with self.get_session() as s:
            if s.query(Currencies).count() == 0:
                s.add_all(
                    [
                        Currencies(
                            currency_name="Ruble",
                            currency_short_name="RUB",
                            currency_sign="₽"
                        ),
                        Currencies(
                            currency_name="Turkish Lira",
                            currency_short_name='TRY',
                            currency_sign="₺"
                        ),
                        Currencies(
                            currency_name="Dollar",
                            currency_short_name='USD',
                            currency_sign="$"
                        )
                    ]
                )
            try:
                adm = s.query(Users).filter(Users.tg_id == admin_id).one()
            except NoResultFound:
                admin = Users(
                    tg_id=admin_id,
                    user_name=admin_name,
                    admin_yn='Y'
                )
                s.add(admin)
                admin_balance = Balances(
                    tg_tg_id=admin_id,
                    curr_curr_id=1
                )
                s.add(admin_balance)
            finally:
                s.commit()

    def get_bot_users(self):
        with self.get_session() as s:
            result = s.query(Users).all()
        return result

    def is_currency(self, curr_short):
        with self.get_session() as s:
            try:
                result = s.query(
                    Currencies.curr_id
                ).filter(
                    Currencies.currency_short_name == curr_short
                ).one()
            except NoResultFound:
                result = -1

        return result > 0

    def update_balance(self, telegram_id, curr_short, amount):
        with self.get_session() as s:
            try:
                blnc = s.query(
                    Balances
                ).filter(
                    Balances.tg_tg_id == telegram_id,
                    Balances.curr_curr_id == Currencies.curr_id,
                    Currencies.currency_short_name == curr_short
                ).one()

                blnc.amount += decimal.Decimal(amount)
                blnc.change_date = datetime.now()

            except NoResultFound:
                curr_id = s.query(Currencies.curr_id).filter(
                    Currencies.currency_short_name == curr_short
                ).one()
                blnc = Balances(
                    tg_tg_id=telegram_id,
                    amount=decimal.Decimal(amount),
                    curr_curr_id=curr_id[0]
                )
                s.add(blnc)
            finally:
                s.commit()

    def get_balance(self, telegram_id):
        with self.get_session() as s:
            result = s.query(
                Users.user_name,
                Balances.amount,
                Currencies.currency_short_name,
                Currencies.currency_sign
            ).filter(
                Users.tg_id == Balances.tg_tg_id,
                Balances.curr_curr_id == Currencies.curr_id,
                Users.tg_id == telegram_id
            ).all()

        return result

    def get_last_exchange_date(self, from_, to_):
        with self.get_session() as s:
            try:
                result = s.query(
                    func.max(ExchangeRates.rate_date)
                ).filter(
                    ExchangeRates.currency_from == from_,
                    ExchangeRates.currency_to == to_
                ).group_by(
                    ExchangeRates.currency_from,
                    ExchangeRates.currency_to
                ).one()
            except NoResultFound:
                print(f"get_last_exchange_date: NoResultFound")
                result = None
            finally:
                return result

    def get_last_exchange_rate(self, from_, to_):
        with self.get_session() as s:
            ex_date = self.get_last_exchange_date(from_, to_)
            try:
                result = s.query(
                    ExchangeRates
                ).filter(
                    ExchangeRates.currency_from == from_,
                    ExchangeRates.currency_to == to_,
                    ExchangeRates.rate_date == ex_date[0]
                ).one()
            except NoResultFound:
                result = None
        return result

    def save_exchange_rate(self, from_, to_, exchange_date, rate_value):
        with self.get_session() as s:
            prev_rate = self.get_last_exchange_date(from_, to_)
            if prev_rate is None or prev_rate[0] < exchange_date:
                rate = ExchangeRates(
                    currency_from=from_,
                    currency_to=to_,
                    rate_date=exchange_date,
                    ex_rate=rate_value
                )
                s.add(rate)
                s.commit()

