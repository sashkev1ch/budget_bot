from datetime import datetime as dt
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton


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
            self._app.add_handler(start_handler)
            self._app.add_handler(balance_handler)
            self._app.add_handler(add_handler)
            self._app.add_handler(sub_handler)
            self._app.add_handler(convert_handler)
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

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.check_cache(update.message.from_user.id)
        # print(update.message.from_user)
        text = ""
        if user:
            text += f"{user.user_name}:\r\n"
            text += self._get_balance_str(user.tg_id)
            await update.message.reply_text(text=text)

    async def convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # /convert rub tl
        # /convert 1000 rub tl
        reply = ""
        user = self.check_cache(update.message.from_user.id)
        if user:
            # cmd_args = context.args
            if len(context.args) == 2:
                cmd_args = [i.upper() for i in context.args]
                self._ex.convert_all(user.tg_id, cmd_args[0], cmd_args[1])
            text = self._get_balance_str(user.tg_id)

            await update.message.reply_text(text)

