import logging
from pathlib import Path
from library import BotClient
from library.database import DbAdapter
from yaml import load, FullLoader

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
config_path = Path(__file__).parent.resolve() / 'configure' / 'config.yml'
with open(config_path, 'r') as file:
    config = load(stream=file, Loader=FullLoader)

db = DbAdapter(
    host=config['db']['host'],
    user=config['db']['user'],
    password=config['db']['password'],
    database=config['db']['database'],
)

db.init_db(
    admin_id=config['bot']['admin_id'],
    admin_name=config['bot']['admin_name']
)

bot = BotClient(
    token=config['bot']['token'],
    admin_id=config['bot']['admin_id'],
    db=db
)
bot.init_bot()


# start_handler = CommandHandler('start', start)
# application.add_handler(start_handler)
# job_q = application.job_queue
# job_q.run_repeating(start, interval=5)
