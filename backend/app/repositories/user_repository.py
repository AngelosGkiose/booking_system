from app.models import UserModel


def get_user_by_email(email,db):
    return db.query(UserModel).filter(UserModel.email == email).first()