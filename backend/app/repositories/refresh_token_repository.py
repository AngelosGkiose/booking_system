from datetime import datetime, timezone

from app.models import RefreshTokenModel


def add_refresh_token(refresh_token,db):
    db.add(refresh_token)

def get_user_refresh_token(user_id,jti,db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.jti == jti,RefreshTokenModel.user_id==user_id).first()

def get_active_user_sessions_repo(user_id,db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.user_id==user_id,RefreshTokenModel.revoked_at.is_(None),RefreshTokenModel.expires_at>datetime.now(timezone.utc)).all()


def get_user_sessions_repo(session_id,user_id,db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.user_id==user_id,RefreshTokenModel.id==session_id).first()


def get_user_all_sessions_repo(user_id,db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.user_id==user_id).all()


def get_all_expired_sessions_repo(db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.expires_at<datetime.now(timezone.utc)).all()



def delete_expired_sessions_repo(session,db):
    db.delete(session)

    