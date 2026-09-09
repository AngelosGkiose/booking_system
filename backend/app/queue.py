from redis import Redis
from rq import Queue

redis_connection=Redis(host="localhost", port=6379)
reservation_queue=Queue("reservations",connection=redis_connection)