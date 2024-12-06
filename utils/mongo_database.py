# utils/mongo_database.py
from pymongo import MongoClient
from datetime import datetime
import os

class MongoDatabase:
   def __init__(self):
       # MongoDBに接続
       mongo_uri = os.getenv('MONGODB_URI')
       print(f"使用する接続URI: {mongo_uri}")  # デバッグ用
       
       if not mongo_uri:
           print("Warning: MONGODB_URI が設定されていません。デフォルトの localhost を使用します。")
           mongo_uri = 'mongodb://localhost:27017/discord_bot'
       
       try:
           self.client = MongoClient(mongo_uri)
           # 接続テスト
           self.client.server_info()
           print("MongoDB接続成功")
       except Exception as e:
           print(f"MongoDB接続エラー: {e}")
           raise

       self.db = self.client.discord_bot
       
       # コレクションの設定
       self.users = self.db.users
       self.history = self.db.gacha_history
       self.settings = self.db.server_settings
       
       # インデックスの作成
       self.users.create_index([("user_id", 1)], unique=True)
       self.history.create_index([("user_id", 1), ("timestamp", -1)])
       self.settings.create_index([("server_id", 1)], unique=True)

   def get_user_data(self, user_id, server_id):
       combined_id = f"{server_id}:{user_id}"
       user_data = self.users.find_one({"user_id": combined_id})
       return user_data

   def update_user_points(self, user_id, server_id, points, last_gacha_date):
       combined_id = f"{server_id}:{user_id}"
       self.users.update_one(
           {"user_id": combined_id},
           {
               "$set": {
                   "points": points,
                   "last_gacha_date": last_gacha_date,
                   "updated_at": datetime.now()
               }
           },
           upsert=True
       )

   def get_server_settings(self, server_id):
       return self.settings.find_one({"server_id": server_id})

   def update_server_settings(self, server_id, settings):
       self.settings.update_one(
           {"server_id": server_id},
           {
               "$set": {
                   "settings": settings,
                   "updated_at": datetime.now()
               }
           },
           upsert=True
       )

   def record_gacha_history(self, user_id, server_id, result_item, points):
       combined_id = f"{server_id}:{user_id}"
       self.history.insert_one({
           "user_id": combined_id,
           "timestamp": int(datetime.now().timestamp()),
           "item_name": result_item['name'],
           "points": points,
           "created_at": datetime.now()
       })

   def close(self):
       """データベース接続を閉じる"""
       self.client.close()

   def __del__(self):
       """デストラクタでも接続を閉じる"""
       try:
           self.client.close()
       except:
           pass