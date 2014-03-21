import os
from datetime import timedelta, date
from celery.signals import celeryd_init

from celery import Celery
from celery.utils.log import get_task_logger
import pymongo
import random

from scrapers.siol import SiolScraper
import config

TIMEOUT_AVG = 0
TIMEOUT_STDDEV = 0

logger = get_task_logger(__name__)

scraper = SiolScraper
db = pymongo.MongoClient(os.getenv('MONGOLAB_URI')).get_default_database()
db.entries.ensure_index([('from_time', pymongo.ASCENDING),
                         ('channel', pymongo.ASCENDING)])
db.descriptions.ensure_index('uuid')

app = Celery('tasks', broker=os.getenv('CLOUDAMQP_URL'))
app.conf.BROKER_POOL_LIMIT = 1
# app.conf.CELERYD_POOL = 'gevent'
app.conf.CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'scrape_worker.start_tasks',
        'schedule': timedelta(days=1),
    },
}

@celeryd_init.connect
def startup_check(**kwargs):
    start_tasks.delay()

@app.task
def start_tasks():
    countdown = 0
    today = date.today()
    dates = [today]
    logger.debug("Channels: " + ", ".join(config.CHANNELS))
    for day in dates:
        for channel in config.CHANNELS:
            if db.tasks.find_one({'date': day.isoformat(), 'channel': channel}):
                logger.debug("Channel %s already has data for %s, skipping."
                             % (channel, day))
            else:
                logger.debug("Scraping channel %s" % channel)
                countdown += random.normalvariate(TIMEOUT_AVG, TIMEOUT_STDDEV)
                update_channel.apply_async(args=[channel, day],
                                           countdown=countdown)
                db.tasks.insert({'date': day.isoformat(), 'channel': channel})

@app.task
def update_channel(channel, day):
    countdown = 0
    new_entries = list(scraper.scrape_channel(channel, day))
    db.entries.insert(new_entries)
    for entry in new_entries:
        countdown += random.normalvariate(TIMEOUT_AVG, TIMEOUT_STDDEV)
        add_description.apply_async(args=[entry['uuid']], countdown=countdown)

@app.task
def add_description(uuid):
    logger.debug("Adding description for %s" % uuid)
    db.descriptions.insert(scraper.scrape_description(uuid))

