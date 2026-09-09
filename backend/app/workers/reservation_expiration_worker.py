from time import sleep
from app.database import SessionLocal
from app.services.reservation_service import expire_pending_reservations_service


def run_worker():
    while True:
        db=SessionLocal()
        try:
            expire_pending_reservations_service(db)
        except Exception as e:
            print(e)
        finally:
            db.close()
        sleep(30)


if __name__ == "__main__":
    run_worker()