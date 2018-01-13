from mastodon import Mastodon
from urllib import parse
import psycopg2
import markovify
import re
import os
import html
from datetime import datetime

mastodon = Mastodon(
    client_id=os.environ['client_id'],
    client_secret=os.environ['client_secret'],
    access_token=os.environ['access_token'],
    api_base_url=os.environ['instance'],
    ratelimit_method='pace',
    ratelimit_pacefactor=1.1
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

# regex to take out html tags
def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


#runs only if it's the first time a user has tried to run the bot
def first_time_setup():
    who_am_i = mastodon.account_verify_credentials()
    who_i_follow = mastodon.account_following(who_am_i['id'])
    origin_userid = who_i_follow[0]['id']
    cur.execute("create table config_data (id varchar(20), value varchar(20))")
    cur.execute("create table toots (text varchar(10000), timestamp timestamp)")
    cur.execute("insert into config_data (id, value) values (%s, %s)", ("userid", origin_userid))
    cur.execute("insert into config_data (id, value) values (%s, %s)", ("setup", True))
    dbconn.commit()
    toots_to_add = []
    first_toots = mastodon.account_statuses(origin_userid)
    previous_request = first_toots[0]['_pagination_prev']['since_id']
    for toot in first_toots:
        clean_toot = toot_cleaner(toot)
        if clean_toot != "":
            toots_to_add.append(clean_toot)
    new_toots = mastodon.fetch_next(first_toots)
    while new_toots is not None:
        for toot in new_toots:
            clean_toot = toot_cleaner(toot)
            if clean_toot != "":
                toots_to_add.append(clean_toot)
        new_toots = mastodon.fetch_next(new_toots)
    for toot_text in toots_to_add:
        cur.execute("insert into toots (text,timestamp) values (%s,%s)", (toot_text, datetime.now()))
    cur.execute("insert into config_data (id, value) values (%s,%s)", ("previous_page", previous_request))
    dbconn.commit()
    print("setup complete")
    mastodon.toot("hello world")

# keep your toots clean and free of html tags
def toot_cleaner(toot):
    if toot['spoiler_text'] == '':
        return remove_tags(toot['content'])
    else:
        return ""


#function that checks a user's timeline for new toots and saves them to the database
def update_toots(userid):
    cur.execute("select value from config_data where id=%s", ("previous_page",))
    previous_page = cur.fetchone()
    previous_dict = {
        'since_id': previous_page[0],
        '_pagination_method': 'GET',
        '_pagination_endpoint': '/api/v1/accounts/' + userid + '/statuses'
    }
    new_toots = mastodon.fetch_previous(previous_dict)
    toots_to_add = []
    while new_toots is not None:
        previous_request = new_toots[0]['_pagination_prev']['since_id']
        for toot in new_toots:
            clean_toot = toot_cleaner(toot)
            if clean_toot != "":
                toots_to_add.append(clean_toot)
        new_toots = mastodon.fetch_previous(new_toots)
    cur.execute("select count() from toots")
    count = cur.fetchone()
    if count[0] > 9950:
        cur.execute(
            "delete from toots where timestamp < ,"
            "(select timestamp from toots order by timestamp limit 1 offset %s)",
            (len(toots_to_add),)
        )
    for toot_text in toots_to_add:
        cur.execute("insert into toots (text,timestamp) values (%s,%s)", (toot_text, datetime.now()))
    cur.execute("update config_data set value = %s where id = %s", (previous_request, "previous_page"))
    dbconn.commit()


# Function that actually generates the toot
def markov_toot():
    cur.execute('select text from toots')
    old_toots = cur.fetchall()
    text = ""
    for toot in old_toots:
        text += toot[0] + "\n"
    text_model = markovify.NewlineText(text)
    toot_to_send = text_model.make_sentence()
    print("tooting the following: " + toot_to_send)
    mastodon.toot(html.unescape(toot_to_send))
