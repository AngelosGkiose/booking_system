from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry as RedisRetry
from rq import Queue

from app.config import settings

redis_connection = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    socket_connect_timeout=3,
    socket_timeout=3,
    retry=RedisRetry(NoBackoff(), retries=0),
)

reservation_queue = Queue("reservations", connection=redis_connection)
