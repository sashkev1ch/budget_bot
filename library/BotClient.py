from pathlib import Path
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardMarkup
from .constants import HELP_MESSAGE, DEFAULT_CURRENCY, DEFAULT_EXCEPTION_REPLY
from .utils import make_excel


def get_keyboard(buttons):
    return InlineKeyboardMarkup([*buttons])


class BotClient:
    def __init__(self, token, admin_id, db, exchanges):
        self._token = token
        self._admin = admin_id
        self._app = None
        self._db = db
        self._ex = exchanges
        self._cache_users = []

    def init_bot(self):
        try:
            self._app = Application.builder().token(self._token).build()

            start_handler = CommandHandler('start', self.start)
            balance_handler = CommandHandler('balance', self.balance)
            add_handler = CommandHandler('add', self.add)
            sub_handler = CommandHandler('sub', self.sub)
            convert_handler = CommandHandler('convert', self.convert)
            help_handler = CommandHandler('help', self.help)
            currencies_handler = CommandHandler('c', self.currencies)
            show_users_handler = CommandHandler('show_users', self.show_users)
            add_user_handler = CommandHandler('add_user', self.add_user)
            del_user_handler = CommandHandler('del_user', self.del_user)
            balance_history_handler = CommandHandler('history', self.get_balance_history)
            self._app.add_handlers(
                [
                    start_handler,
                    balance_handler,
                    add_handler,
                    sub_handler,
                    convert_handler,
                    help_handler,
                    currencies_handler,
                    show_users_handler,
                    add_user_handler,
                    del_user_handler,
                    balance_history_handler,
                    MessageHandler(filters.TEXT, self.fast_add)
                ]
            )
            self.update_cache()
            self._app.run_polling()
        except Exception as e:
            print(f"init_bot: {e}")
            raise

    async def fast_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        amount = None
        try:
            amount = int(update.message.text)

        except ValueError:
            await update.message.reply_text(update.message.text)

        user = self.check_cache(update.message.from_user.id)

        if user and amount:
            result, err = self._db.update_balance(
                telegram_id=user.tg_id,
                curr_short=DEFAULT_CURRENCY,
                amount=amount
            )
            if not err:
                reply = f"{DEFAULT_CURRENCY} balance updated for {amount}\r\n" \
                        f"{self._get_balance_str(user.tg_id)}"
            else:
                reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

            await update.message.reply_text(reply)

    def update_cache(self):
        self._cache_users, err = self._db.get_bot_users()

    def check_cache(self, telegram_id):
        for user in self._cache_users:
            if user.tg_id == telegram_id:
                return user
        return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user:
            await update.message.reply_text(f"Hi {user.name}")

    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        reply = ""
        if user:
            cmd_args = context.args

            try:
                amount = float(cmd_args[0])
                try:
                    currency = cmd_args[1].upper()
                except IndexError:
                    currency = DEFAULT_CURRENCY

                result, err = self._db.update_balance(
                    telegram_id=user.tg_id,
                    curr_short=currency,
                    amount=amount
                )

                if not err:
                    reply += f"subtracted {amount} {currency}\r\n"
                    reply += self._get_balance_str(user.tg_id)
                else:
                    reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

            except IndexError:
                reply = f"not enough arguments: {cmd_args}"

        await update.message.reply_text(reply)

    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = ""
        user = self.check_cache(update.message.from_user.id)
        if user:
            cmd_args = context.args
            try:
                amount = float(cmd_args[0])
                try:
                    currency = cmd_args[1].upper()
                except IndexError:
                    currency = DEFAULT_CURRENCY

                result, err = self._db.update_balance(
                    telegram_id=user.tg_id,
                    curr_short=currency,
                    amount=-amount
                )
                if not err:
                    reply += f"subtracted {amount} {currency}\r\n"
                    reply += self._get_balance_str(user.tg_id)
                else:
                    reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

            except IndexError:
                reply = f"not enough arguments: {cmd_args}"

        await update.message.reply_text(f"{reply}")

    def _get_balance_str(self, telegram_id):
        reply = ""
        user_balance, err = self._db.get_balance(telegram_id)
        if not err:
            for i, blnc in enumerate(user_balance, 1):
                reply += f"{i}. {blnc[1]} {blnc[2]}\r\n"
        else:
            reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

        return reply

    def _get_currencies_str(self):
        currencies, err = self._db.get_currencies()
        if not err:
            reply = ", ".join([f"{i[0]}" for i in currencies])
        else:
            reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

        return reply

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        # print(update.message.from_user)
        text = ""
        if user:
            user_balance = self._get_balance_str(user.tg_id)
            text += f"{user.user_name}:\r\n{user_balance}"
            await update.message.reply_text(text=text)

    async def currencies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.check_cache(update.message.from_user.id):
            text = self._get_currencies_str()
            await update.message.reply_text(text=text)

    async def convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # /convert rub tl
        # /convert 1000 rub tl
        user = self.check_cache(update.message.from_user.id)
        if user:
            if len(context.args) == 2:
                cmd_args = [i.upper() for i in context.args]
                self._ex.convert_all(user.tg_id, cmd_args[0], cmd_args[1])
            text = self._get_balance_str(user.tg_id)

            await update.message.reply_text(text)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user:
            await update.message.reply_text(HELP_MESSAGE)

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user and user.admin_yn == 'Y':
            try:
                new_user_name = context.args[0]
                new_user_tg_id = context.args[1]

                try:
                    new_user_adm = context.args[2]
                except IndexError:
                    new_user_adm = 'N'

                result, err = self._db.create_user(new_user_name, new_user_tg_id, new_user_adm)

                if not err:
                    self.update_cache()
                    reply = f"new user {new_user_name} created"
                else:
                    reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}"

            except IndexError:
                reply = "No user name passed"

            await update.message.reply_text(reply)

    async def del_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user and user.admin_yn == 'Y':
            try:
                user_tg_id = int(context.args[0])
                result, err = self._db.drop_user(user_tg_id)
                if not err:
                    self.update_cache()
                    reply = "User dropped"
                else:
                    reply = f"{DEFAULT_EXCEPTION_REPLY}: {err}: "

            except IndexError:
                reply = "No Telegram Id passed"

            await update.message.reply_text(reply)

    async def show_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user and user.admin_yn == 'Y':
            users, err = self._db.get_bot_users()
            reply = ''.join(
                [
                    f"{i} || "
                    f"tg_id: {user.tg_id} || "
                    f"name: {user.user_name} || "
                    f"admin_yn: {user.admin_yn.upper()}\r\n"
                    for i, user in enumerate(users, 1)
                ]
            )
            await update.message.reply_text(reply)

    async def get_balance_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user:
            try:
                currency = context.args[0].upper()
            except IndexError:
                currency = DEFAULT_CURRENCY

            balances, err = self._db.get_balance_history(user.tg_id, currency)
            if not err:
                history = [
                    (
                        balance.change_date,
                        balance.update_value,
                        balance.amount
                    )
                    for balance in balances
                ]
                file_path = Path(__file__).parent.resolve() /'..' / 'budget_reports' / 'budget.xlsx'
                make_excel(file_path, history)
                budget_file = open(file_path, 'rb')
                await context.bot.send_document(
                    chat_id=user.tg_id,
                    document=budget_file
                )
            else:
                await update.message.reply_text(f'{DEFAULT_EXCEPTION_REPLY}: {err}')
