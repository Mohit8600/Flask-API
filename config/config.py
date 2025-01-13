import os
from dotenv import load_dotenv

load_dotenv()

class config:
   JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
   JWT_ACCESS_TOKEN_EXPIRES = 10800
   FIREBASE_CONFIG = 'article-writing-key.json'