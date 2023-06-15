import json
import requests
import datetime


class BotExchanges:
    def __init__(self, api_key, db):
        self._key = api_key
        self._db = db

    def get_exchange_rate(self, from_, to_):
        r = requests.get(f"https://api.apilayer.com/fixer/latest?base={from_}&symbols={to_}",
                         headers={"apikey": self._key},
                         timeout=5)
        res = json.loads(r.text)
        print(res)
        print(res['rates'][to_])

    def convert_all(self, telegram_id, from_, to_):
        try:
            r = requests.get(f"https://api.apilayer.com/fixer/latest?base={from_}&symbols={to_}",
                             headers={"apikey": self._key},
                             timeout=5)
            res = json.loads(r.text)
        except requests.exceptions.ReadTimeout:
            res = {'success': False}

        if res['success']:
            print(f"success = {res['success']}")
            self._db.save_exchange_rate(
                from_,
                to_,
                datetime.datetime.strptime(res['date'], '%Y-%m-%d').date(),
                res['rates'][to_]
            )

        exchange_rate = self._db.get_last_exchange_rate(from_, to_)
        new_amount = 0
        balances = self._db.get_balance(telegram_id)
        for blnc in balances:
            if blnc[2] == from_:
                old_amount = blnc[1]
                new_amount = blnc[1] * exchange_rate.ex_rate
        self._db.update_balance(telegram_id, to_, new_amount)
        self._db.update_balance(telegram_id, from_, -old_amount)

    def get_symbols(self):
        r = requests.get("https://api.apilayer.com/fixer/symbols",
                         headers={"apikey": self._key})
        res = r.text
        print(res['rates'])
