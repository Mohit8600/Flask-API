from flask import jsonify, request
from utils.helpers import hash_password, verify_password,generate_token,Admin,is_admin
from datetime import datetime,timezone, timedelta
import uuid
from services.firebase_service import init_firebase
from flask_jwt_extended import jwt_required, get_jwt_identity


def register_routes(app):

  db = init_firebase()

  @app.route("/")
  def default():
    return {
      "msg" : "This is defualt response!."
    }, 200
  

  @app.route('/singup', methods=['POST'])
  def singup():
    try:
      User = request.get_json()
      name = User['name']
      email = User['email']
      password = User['password']
      role = User.get('role','user')
      is_deleted = False

      if not email or not password:
        return jsonify({"error": "Email and password are requred"}),400
      
      User_query = db.collection('User').where('email', '==', email).get()
      if User_query:
        return jsonify({"error": "user already exists"}), 409
      
      hashed_password = hash_password(password)

      created_at = datetime.now(timezone.utc)
      updated_at = datetime.now(timezone.utc)

      uid =str(uuid.uuid4())
      doc_User ={
        "uuid": uid,
        "name": name,
        "email": email,
        "password":hashed_password.decode('utf-8'),
        "created_at": created_at,
        "updated_at": updated_at,
        "is_deleted": is_deleted,
        "role": role
      }

      db.collection('User').document(uid).set(doc_User)
      return jsonify({"msg": "user created successfully", "uid":uid, "role": role}),201
    except Exception as e:
      return jsonify({'error': str(e)}), 500
    

  @app.route('/login', methods=['POST'])
  def login():
      try:
          User_data = request.get_json()
          email = User_data.get('email')
          password = User_data.get('password')

          if not email or not password:
              return jsonify({"error": "Email and password are required"}), 400

          User_query = db.collection('User').where('email', '==', email).get()

          if not User_query:
              return jsonify({"error": "User does not exist"}), 404
          User_doc = User_query[0].to_dict()

          if User_doc.get("is_deleted", False):
              return jsonify({"msg": "User has deleted"}),403
      

          if not verify_password(password, User_doc['password'].encode('utf-8')):
              return jsonify({"error": "Invalid password"}), 401

          access_token = generate_token(user_id=User_doc['uuid'], role = User_doc['role'] )
          return jsonify({"msg": "Login successful", "token":access_token, "role": User_doc['role']}), 200

      except Exception as e:
          return jsonify({"error": str(e)}),500
      
  @app.route('/all_user', methods=['GET'])
  # @jwt_required()
  @Admin
  def all_User():
      try:
         
          User_ref = db.collection('User').where("is_deleted", "==", False).stream()

          User_list =[]

          for User in User_ref:
              User_data = User.to_dict()
              User_list.append({
                  "uuid": User_data.get('uuid'),
                  "email": User_data.get('email'),
                  "created_at": User_data.get('created_at'),
                  "updated_at": User_data.get('updated_at'),
                  "password":User_data.get('password')
              })

          return jsonify({"user": User_list}), 200
      except Exception as e:
          return jsonify({"error": str(e)}), 500
      
  @app.route('/deleted/<user_id>', methods=['DELETE'])
  # @jwt_required()
  @Admin
  def User_delete(user_id):
      try:
          User_ref = db.collection('User').document(user_id)
          User = User_ref.get()

          if User.exists:
              User_data = User.to_dict()
              if User_data.get("is_deleted")== True:
                  return jsonify({"msg": "Faild to detect user"}),500
              
              User_ref.update({
                  "is_deleted": True,
                  "updated_at": datetime.now(timezone.utc).isoformat()
              })
              return jsonify({"msg": "user deleted successfully"}),200
          else:
              return jsonify({"error": "user not found"}),404
      except Exception as e:
          return jsonify({"error": str(e)}),500
      
  @app.route('/user/<uuid_id>', methods=["PUT","GET"])
  # @Admin
  def User_info(uuid_id):
      if request.method == 'PUT':
          try:
              User_ref = db.collection('User').document(uuid_id)
              User = User_ref.get()

              if User.exists:
                  Userr =request.get_json()
                
                  if User.to_dict().get("is_deleted", False):
                      return jsonify({"error": "Cannot update a deleted user"}), 400

                  update_User ={
                      "name":Userr.get("name",User.to_dict().get("name")),
                      "email":Userr.get("email",User.to_dict().get("email")),
                      "updated_at": datetime.now(timezone.utc).isoformat()
                  }

                  User_ref.update(update_User)
                  return jsonify({"msg": "User updated successfully", "User": update_User}),200
              else:
                  return jsonify({"error": "User not found"}), 404
            
          except Exception as e:
              return jsonify({"error": str(e)}),500
        
      else:
  # def get_user_info(uuid_id):
          try:
              user_ref = db.collection('User').document(uuid_id).get()
              
              if user_ref.exists:
                  user_data = user_ref.to_dict()
                  return jsonify({
                      "uuid": user_data.get('uuid'),
                      "name": user_data.get('name'),
                      "email": user_data.get('email'),
                      "created_at": user_data.get('created_at'),
                      "updated_at": user_data.get('updated_at'),
                      "role": user_data.get('role')
                  }), 200
              else:
                  return jsonify({"error": "User not found"}), 404
          except Exception as e:
              return jsonify({"error": str(e)}), 500

#  #  Cetegory #   #


  @app.route('/create/category', methods=['POST'])
  @jwt_required()
  def create_category():
      try:
          current_user_uuid = get_jwt_identity()
          category_data = request.get_json()
          category_name = category_data.get('name')
          description = category_data.get('description')
          is_deleted = False

          if not category_name:
              return jsonify({"error": "Category name is required"}), 400

          category_id = str(uuid.uuid4())
          is_deleted = False

          category_doc = {
              "uuid": category_id,
              "name": category_name,
              "description": description,
              "user_id": current_user_uuid,  
              "is_deleted": is_deleted,
              "created_at": datetime.now(timezone.utc).isoformat()
          }

          db.collection('Categories').document(category_id).set(category_doc)

          return jsonify({"msg": "Category created successfully", "category_id": category_id}), 201
      except Exception as e:
          return jsonify({"error": str(e)}), 500


  @app.route('/user/categories', methods=['GET'])
  @jwt_required()
  def get_categories_by_user():
      try:
          current_user_uuid = get_jwt_identity()

          categories_ref = db.collection('Categories').where("user_id", "==", current_user_uuid).where("is_deleted", "==", False).stream()

          categories = []
          for category in categories_ref:
              categories.append(category.to_dict())

          return jsonify({"categories": categories}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500
      

  @app.route('/update/category/<category_id>', methods=['PUT'])
  @jwt_required()
  def update_category(category_id):
      try:
          current_user_uuid = get_jwt_identity()

          category_ref = db.collection('Categories').document(category_id)
          category = category_ref.get()

          if not category.exists:
              return jsonify({"error": "Category not found"}), 404

          category_data = category.to_dict()

          if category_data['user_id'] != current_user_uuid and not is_admin(current_user_uuid):
              return jsonify({"error": "Unauthorized"}), 403
          
          if category_data.get("is_deleted", False):
              return jsonify({"msg": "category has deleted"}),403

          update_data = request.get_json()
          category_ref.update({
              "name": update_data.get('name', category_data['name']),
              "description": update_data.get('description', category_data['description']),
              "updated_at": datetime.now(timezone.utc).isoformat()
          })

          return jsonify({"msg": "Category updated successfully"}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500


  @app.route('/deleted/category/<category_id>', methods=['DELETE'])
  @jwt_required()
  def delete_category(category_id):
      try:
          current_user_uuid = get_jwt_identity()

          category_ref = db.collection('Categories').document(category_id)
          category = category_ref.get()

          if not category.exists:
              return jsonify({"error": "Category not found"}), 404

          category_data = category.to_dict()

          if category_data['user_id'] != current_user_uuid and not is_admin(current_user_uuid):
              return jsonify({"error": "Unauthorized"}), 403

          category_ref.update({
              "is_deleted": True,
              "updated_at": datetime.now(timezone.utc).isoformat()
          })

          return jsonify({"msg": "Category deleted successfully"}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500
      
  @app.route('/all_categories', methods=['GET'])
  @Admin
  def get_all_categories():
      try:
          categories = db.collection('Categories').where("is_deleted", "==", False).stream()
          category_list = [category.to_dict() for category in categories]
          return jsonify({"categories": category_list}), 200
      except Exception as e:
          return jsonify({"error": str(e)}), 500

  

#     #     Article   #       #

  @app.route('/create/articles', methods=['POST'])
  @jwt_required()
  def create_article():
      try:
          current_user_uuid = get_jwt_identity()
          article_data = request.get_json()

          title = article_data.get('title')
          content = article_data.get('content')
          category_id = article_data.get('category_id')
          is_deleted = False
          

          if not title or not content or not category_id:
              return jsonify({"error": "Title , content and category_id are required"}), 400

          category_ref = db.collection('Categories').document(category_id).get()
          if not category_ref.exists:
              return jsonify({"error": "Invalid category_id"}), 404

          article_id = str(uuid.uuid4())

          article_doc = {
              "uuid": article_id,
              "title": title,
              "content": content,
              "user_id": current_user_uuid,
              "category_id": category_id,
              "is_deleted": is_deleted, 
              "created_at": datetime.now(timezone.utc).isoformat(),
              "updated_at": datetime.now(timezone.utc).isoformat()
          }

          db.collection('Articles').document(article_id).set(article_doc)

          return jsonify({"msg": "Article created successfully", "article_id": article_id}), 201

      except Exception as e:
          return jsonify({"error": str(e)}), 500



  @app.route('/user/articles', methods=['GET'])
  @jwt_required()
  def get_articles_by_user():
      try:
          current_user_uuid = get_jwt_identity()

          articles_ref = db.collection('Articles').where("user_id", "==", current_user_uuid).where("is_deleted", "==", False).stream()

          articles = []
          for article in articles_ref:
              articles.append(article.to_dict())

          return jsonify({"articles": articles}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500


  @app.route('/category/articles/<category_id>', methods=['GET'])
  def get_articles_by_category(category_id):
      try:
          current_user_uuid = get_jwt_identity()
          if current_user_uuid and is_admin(current_user_uuid):
              articles_ref = db.collection('Articles').where("category_id", "==", category_id).stream()
          else:
              articles_ref = db.collection('Articles').where("category_id", "==", category_id).where("is_deleted", "==", False).stream()

          articles = []
          for article in articles_ref:
              articles.append(article.to_dict())

          return jsonify({"articles": articles}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500

  @app.route('/update/articles/<article_id>', methods=['PUT'])
  @jwt_required()
  def update_article(article_id):
      try:
          current_user_uuid = get_jwt_identity()

        
          article_ref = db.collection('Articles').document(article_id)
          article = article_ref.get()

          if not article.exists:
              return jsonify({"error": "Article not found"}), 404

          article_data = article.to_dict()

          
          if article_data['user_id'] != current_user_uuid and not is_admin(current_user_uuid):
              return jsonify({"error": "Unauthorized"}), 403

          
          update_data = request.get_json()
          article_ref.update({
              "title": update_data.get('title', article_data['title']),
              "content": update_data.get('content', article_data['content']),
              "is_deleted": update_data.get('is_deleted', article_data['is_deleted']),
              "updated_at": datetime.now(timezone.utc).isoformat()
          })

          return jsonify({"msg": "Article updated successfully"}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500


  @app.route('/delete/articles/<article_id>', methods=['DELETE'])
  @jwt_required()
  def delete_article(article_id):
      try:
          current_user_uuid = get_jwt_identity()

          
          article_ref = db.collection('Articles').document(article_id)
          article = article_ref.get()

          if not article.exists:
              return jsonify({"error": "Article not found"}), 404

          article_data = article.to_dict()

          
          if article_data['user_id'] != current_user_uuid and not is_admin(current_user_uuid):
              return jsonify({"error": "Unauthorized"}), 403

          
          article_ref.update({
              "is_deleted": True,
              "updated_at": datetime.now(timezone.utc).isoformat()
          })

          return jsonify({"msg": "Article deleted successfully"}), 200

      except Exception as e:
          return jsonify({"error": str(e)}), 500