import shlex
from datetime import datetime, date
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
from library.database.models import Base
from library.database.models.schema import Balances, Currencies, ExchangeRates, Users, BalanceHistory
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
                s.query(Users).filter(Users.tg_id == admin_id).one()
            except NoResultFound:
                operation_date = datetime.now()
                admin = Users(
                    tg_id=admin_id,
                    user_name=admin_name,
                    admin_yn='Y'
                )
                s.add(admin)
                admin_balance = Balances(
                    tg_tg_id=admin_id,
                    curr_curr_id=1,
                    create_date=operation_date,
                    change_date=operation_date

                )
                s.add(admin_balance)
                blnc = s.query(Balances).filter(
                    Balances.tg_tg_id == admin_id,
                    Balances.curr_curr_id == 1,
                    Balances.create_date == operation_date,
                    Balances.change_date == operation_date
                ).one()

                balance_history = BalanceHistory(
                    blnc_blnc_id=blnc.blnc_id,
                    curr_curr_id=blnc.curr_curr_id,
                    change_date=blnc.change_date
                )

                s.add(balance_history)

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
                operation_date = datetime.now()
                blnc = s.query(
                    Balances
                ).filter(
                    Balances.tg_tg_id == telegram_id,
                    Balances.curr_curr_id == Currencies.curr_id,
                    Currencies.currency_short_name == curr_short
                ).one()

                blnc.amount += decimal.Decimal(amount)
                blnc.change_date = operation_date

                blnc_history = BalanceHistory(
                    blnc_blnc_id=blnc.blnc_id,
                    curr_curr_id=blnc.curr_curr_id,
                    change_date=operation_date,
                    amount=blnc.amount,
                    update_value=amount
                )

                s.add(blnc_history)

            except NoResultFound:
                try:
                    curr_id = s.query(Currencies.curr_id).filter(
                        Currencies.currency_short_name == curr_short.upper()
                    ).one()
                    blnc = Balances(
                        tg_tg_id=telegram_id,
                        amount=decimal.Decimal(amount),
                        curr_curr_id=curr_id[0]
                    )
                    s.add(blnc)


                    blnc = s.query(Balances).filter(
                        Balances.tg_tg_id==telegram_id,
                        Balances.curr_curr_id==curr_id[0]
                    ).one()

                    blnc_history = BalanceHistory(
                        blnc_blnc_id=blnc.blnc_id,
                        curr_curr_id=blnc.curr_curr_id,
                        change_date=operation_date,
                        amount=blnc.amount,
                        update_value=amount
                    )

                    s.add(blnc_history)
                except Exception as err:
                    print(err)
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

    def get_currencies(self):
        with self.get_session() as s:
            result = s.query(
                Currencies.currency_short_name
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
                print("get_last_exchange_date: NoResultFound")
                result = None

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

    def create_user(self, user_name, user_tg_id, admin_yn):
        operation_date = datetime.now()
        with self.get_session() as s:
            user = Users(
                tg_id=user_tg_id,
                user_name=user_name,
                admin_yn=admin_yn,
                create_date=operation_date
            )
            s.add(user)
            user_balance = Balances(
                tg_tg_id=user_tg_id,
                curr_curr_id=1,
                create_date=operation_date,
                change_date=operation_date
            )
            s.add(user_balance)

            try:
                user_balance = s.query(Balances).filter(
                    Balances.tg_tg_id==user_tg_id,
                    Balances.curr_curr_id==1
                ).one()

                balance_hist = BalanceHistory(
                        blnc_blnc_id=user_balance.blnc_id,
                        curr_curr_id=user_balance.curr_curr_id,
                        change_date=operation_date,
                        amount=user_balance.amount
                    )

                s.add(balance_hist)

                s.commit()
            except Exception as err:
                print(err)
        return True

    def drop_user(self, telegram_id):
        with self.get_session() as s:
            try:
                # get objects
                balances = s.query(Balances).filter_by(tg_tg_id=telegram_id).all()
                balance_history = s.query(BalanceHistory).filter_by(blnc_blnc_id=balances[0].blnc_id).all()
                user = s.query(Users).filter_by(tg_id=telegram_id).one()

                # delete objects
                for hist in balance_history:
                    s.delete(hist)
                for balance in balances:
                    s.delete(balance)

                s.delete(user)

                s.commit()
            except Exception as err:
                print(err)
                return False
        return True

    def get_balance_history(self, telegram_id, currency):
        with self.get_session() as s:
            try:
                result = s.query(
                    BalanceHistory
                ).join(
                    Balances
                ).join(
                    Currencies
                ).filter(
                    Balances.tg_tg_id == telegram_id,
                    Currencies.currency_short_name == currency
                ).order_by(
                    BalanceHistory.change_date.desc()
                ).all()
            except Exception as err:
                print(err)

        return result
