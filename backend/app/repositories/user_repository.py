from app.models import UserModel


def get_user_by_email(email,db):
    return db.query(UserModel).filter(UserModel.email == email).first()



def add_user(new_user,db):
    db.add(new_user)

def get_user_by_id(user_id,db):
    return db.query(UserModel).filter(UserModel.id == user_id).first()