from datetime import datetime as dt
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from .constants import HELP_MESSAGE


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
            self._app.add_handler(start_handler)
            self._app.add_handler(balance_handler)
            self._app.add_handler(add_handler)
            self._app.add_handler(sub_handler)
            self._app.add_handler(convert_handler)
            self._app.add_handler(help_handler)
            self._app.add_handler(currencies_handler)
            self._app.add_handler(show_users_handler)
            self._app.add_handler(add_user_handler)
            self._app.add_handler(del_user_handler)
            self.update_cache()
            self._app.run_polling()
        except Exception as e:
            print(f"init_bot: {e}")
            raise

    def update_cache(self):
        self._cache_users = self._db.get_bot_users()

    def check_cache(self, telegram_id):
        for user in self._cache_users:
            if user.tg_id == telegram_id:
                return user
        return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.from_user.id == self._admin:
            admin_name = update.message.from_user.first_name
            print(update.message.text)
            # print(admin_name)
            await update.message.reply_text(f"Hi {admin_name}")

    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = ""
        user = self.check_cache(update.message.from_user.id)
        if user:
            cmd_args = context.args
            if len(cmd_args) == 2:
                self._db.update_balance(
                    telegram_id=user.tg_id,
                    curr_short=cmd_args[1].upper(),
                    amount=float(cmd_args[0])
                )
                reply += f"added {cmd_args[0]} {cmd_args[1]}\r\n"
                reply += self._get_balance_str(user.tg_id)
            else:
                reply += f"not enough arguments: {cmd_args}"
        else:
            reply += f"unknown user: {update.message.from_user}"

        await update.message.reply_text(f"{reply}")

    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply = ""
        user = self.check_cache(update.message.from_user.id)
        if user:
            cmd_args = context.args
            if len(cmd_args) == 2:
                self._db.update_balance(
                    telegram_id=user.tg_id,
                    curr_short=cmd_args[1].upper(),
                    amount=-float(cmd_args[0])
                )
                reply += f"subtracted {cmd_args[0]} {cmd_args[1]}\r\n"
                reply += self._get_balance_str(user.tg_id)
            else:
                reply += f"not enough arguments: {cmd_args}"
        else:
            reply += f"unknown user: {update.message.from_user}"

        await update.message.reply_text(f"{reply}")

    def _get_balance_str(self, telegram_id):
        text = ""
        user_balance = self._db.get_balance(telegram_id)
        for i, blnc in enumerate(user_balance, 1):
            text += f"{i}. {blnc[1]} {blnc[2]}\r\n"
        return text

    def _get_currencies_str(self):
        currencies = self._db.get_currencies()
        return ", ".join([f"{i[0]}" for i in currencies])

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
        if user and user.tg_id == self._admin:
            try:
                new_user_name = context.args[0]
                new_user_tg_id = context.args[1]

                try:
                    new_user_adm = context.args[2]
                except IndexError:
                    new_user_adm = 'N'

                if self._db.create_user(new_user_name, new_user_tg_id, new_user_adm):
                    self.update_cache()
                    reply = f"new user {new_user_name} created"
                else:
                    reply = "something went wrong"

            except IndexError:
                reply = "No user name passed"

            await update.message.reply_text(reply)

    async def show_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user and user.tg_id == self._admin:
            users = self._db.get_bot_users()
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

    async def del_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        if user and user.admin_yn == 'Y':
            try:
                user_tg_id = int(context.args[0])
                if self._db.drop_user(user_tg_id):
                    self.update_cache()
                    reply = "User dropped"
                else:
                    reply = "something went wrong"

            except IndexError:
                reply = "No Telegram Id passed"

            await update.message.reply_text(reply)
