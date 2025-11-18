from django.conf import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGO_URI)
print(settings.MONGO_URI)
mongo_db = client[settings.MONGO_DB]

users_collection = mongo_db[settings.MONGO_COLLECTION_USERS]
logs_collection = mongo_db[settings.MONGO_COLLECTION_LOGS]
