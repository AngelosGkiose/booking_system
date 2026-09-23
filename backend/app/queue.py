from redis import Redis
from redis.retry import Retry as RedisRetry
from redis.backoff import NoBackoff
from rq import Queue
from config import settings

redis_connection = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    socket_connect_timeout=3,
    socket_timeout=3,
    retry=RedisRetry(
        NoBackoff(),
        retries=0
    )
)

reservation_queue = Queue(
    "reservations",
    connection=redis_connection
)