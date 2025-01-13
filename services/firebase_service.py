from flask import Flask
from config.config import config
import firebase_admin
from firebase_admin import credentials,firestore


def init_firebase():
  if not firebase_admin._apps:
    cred = credentials.Certificate(config.FIREBASE_CONFIG)
    firebase_admin.initialize_app(cred)
  return firestore.client()