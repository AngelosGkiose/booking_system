from rq import Repeat, Retry

from app.jobs.monitoring_jobs import monitor_failed_outbox_events_job
from app.jobs.refresh_token_job import refresh_token_cleanup_job
from app.queue import reservation_queue
from rq.job import Job
from rq.exceptions import NoSuchJobError

def job_exists(job_id):
    try:
        Job.fetch(job_id, connection=reservation_queue.connection)
        return True
    except NoSuchJobError:
        return False

def schedule_jobs():
    if not job_exists("refresh_token_cleanup"):

        reservation_queue.enqueue(
            refresh_token_cleanup_job,
            job_id="refresh_token_cleanup",
            repeat=Repeat(times=365, interval=86400),
            retry=Retry(max=3, interval=[10, 30, 60])
        )

    if not job_exists("monitor_failed_outbox_events"):
        reservation_queue.enqueue(
            monitor_failed_outbox_events_job,
            job_id="monitor_failed_outbox_events",
            repeat=Repeat(times=365, interval=60),
            retry=Retry(max=3, interval=[10, 30, 60])
        )

if __name__ == "__main__":
    schedule_jobs()