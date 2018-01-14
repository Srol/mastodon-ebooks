from rq import Queue
from worker import conn
from utils import regenerate_corpus

q = Queue(connection=conn)
q.enqueue(regenerate_corpus, timeout=1800)