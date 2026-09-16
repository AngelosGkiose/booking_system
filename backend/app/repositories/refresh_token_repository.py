from app.models import RefreshTokenModel


def add_refresh_token(refresh_token,db):
    db.add(refresh_token)

def get_user_refresh_token(user_id,jti,db):
    return db.query(RefreshTokenModel).filter(RefreshTokenModel.jti == jti,RefreshTokenModel.user_id==user_id).first()