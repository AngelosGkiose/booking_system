from rq import Repeat, Retry

from app.jobs.refresh_token_job import refresh_token_cleanup_job
from app.queue import reservation_queue

reservation_queue.enqueue(
    refresh_token_cleanup_job,
    repeat=Repeat(times=365, interval=86400),
    retry=Retry(max=3, interval=[10, 30, 60])
)