from mastodon import Mastodon
import random
import os
from urllib import parse
from worker import conn
import psycopg2
from utils import first_time_setup, update_toots, markov_toot
from rq import Queue

# setting up the redis, mastodon and postgres connections
q = Queue(connection=conn)
mastodon = Mastodon(
    client_id=os.environ['client_id'],
    client_secret=os.environ['client_secret'],
    access_token=os.environ['access_token'],
    api_base_url='https://botsin.space'
)
parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])
dbconn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = dbconn.cursor()

#this is a check to see if it's the first timne a user's run the bot, so the script knows to do db setup
try:
    cur.execute("select value from config_data where id=%s", ("setup",))
except psycopg2.ProgrammingError:
    first_time = True
else:
    first_time = False


if first_time:
    q.enqueue(first_time_setup, timeout=1800)
else:
    cur.execute("select value from config_data where id=%s", ("userid",))
    userid = cur.fetchone()
    userid = userid[0]
    q.enqueue(update_toots, userid, timeout=900)
    if random.randint(1, 4) == 1:
        q.enqueue(markov_toot, timeout=900)
        print("generating toot")
    else:
        print("Not tooting this hour.")

dbconn.close()
