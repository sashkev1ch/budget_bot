from datetime import datetime as dt
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton


def get_keyboard(buttons):
    return InlineKeyboardMarkup([*buttons])


class BotClient:
    def __init__(self, token, admin_id, db):
        self._token = token
        self._admin = admin_id
        self._app = None
        self._db = db
        self._cache_users = []

    def init_bot(self):
        try:
            self._app = Application.builder().token(self._token).build()
            start_handler = CommandHandler('start', self.start)
            self._app.add_handler(start_handler)
            add_handler = CommandHandler('add', self.add)
            self._app.add_handler(add_handler)
            self.update_cache()
            self._app.run_polling()
        except Exception as e:
            print(f"init_bot: {e}")
            raise

    def update_cache(self):
        self._cache_users = self._db.get_bot_users()

    def check_cache(self, telegram_id):
        for i in self._cache_users:
            if i.tg_id == telegram_id:
                return i
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
                    curr_short=cmd_args[1],
                    amount=float(cmd_args[0])
                )
                reply += f"added {cmd_args[0]} {cmd_args[1]}"
            else:
                reply += f"not enough arguments: {cmd_args}"
        else:
            reply += f"unknown user: {update.message.from_user}"

        await update.message.reply_text(f"{reply }")


