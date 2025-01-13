import bcrypt
from functools import wraps
import jwt
from datetime import datetime,timedelta
from flask_jwt_extended import  create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, current_app
from services.firebase_service import init_firebase

db = init_firebase()

def hash_password(password):
  return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password,hashed):
  return bcrypt.checkpw(password.encode('utf-8'),hashed)

def is_admin(user_id):
    user_ref = db.collection('User').document(user_id).get()
    user_data = user_ref.to_dict()
    return user_data.get('role') == 'admin' if user_data else False

def Admin(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        # try:
        #     JWT_User = get_jwt() 
        #     if  JWT_User.get('role') != 'Admin':
        #         return jsonify({"msg": "Invalid request"}),403
        # except Exception as e:
        #     return jsonify({"msg": "Invalid request"}),403
        current_user_uuid = get_jwt_identity()

        if not is_admin(current_user_uuid):
            return jsonify({"error": "Admin privileges required"}), 403
        return func(*args, **kwargs)
    return wrapper


def generate_token(user_id, role):
  addition_claims = {
     'role' : role
  }
  return create_access_token(identity=user_id, additional_claims=addition_claims)
 
