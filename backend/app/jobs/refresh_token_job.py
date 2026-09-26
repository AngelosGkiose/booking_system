from app.database import SessionLocal
from app.services.auth_service import delete_all_expired_sessions_background_service


def refresh_token_cleanup_job():
    db = SessionLocal()
    try:
        return delete_all_expired_sessions_background_service(db)
    finally:
        db.close()
