from pymongo import MongoClient

MONGO_URI = "mongodb+srv://avargas28_db_user:jOQrKhZE4AKgiY08@cluster0.zdyti9q.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)

try:
    client.admin.command("ping")
    print("✅ Conexión OK")
except Exception as e:
    print("❌ Error:", e)
