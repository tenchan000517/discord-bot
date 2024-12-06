import sqlite3
import json
from datetime import datetime
import os
from typing import Optional, Dict, List

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """データベーステーブルの初期化"""
        conn = self.get_connection()
        c = conn.cursor()

        # サーバー設定テーブル
        c.execute('''CREATE TABLE IF NOT EXISTS servers
                    (server_id TEXT PRIMARY KEY,
                     settings TEXT)''')

        # ユーザーデータテーブル
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (user_id TEXT,
                     server_id TEXT,
                     points INTEGER DEFAULT 0,
                     last_gacha_date TEXT,
                     PRIMARY KEY (user_id, server_id))''')

        conn.commit()
        conn.close()

    def get_server_settings(self, server_id: str) -> Optional[Dict]:
        """サーバーの設定を取得"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT settings FROM servers WHERE server_id = ?", (server_id,))
        result = c.fetchone()
        
        conn.close()
        return json.loads(result[0]) if result else None

    def update_server_settings(self, server_id: str, settings: Dict):
        """サーバーの設定を更新"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("""INSERT OR REPLACE INTO servers (server_id, settings)
                    VALUES (?, ?)""", (server_id, json.dumps(settings)))
        
        conn.commit()
        conn.close()

    def get_user_data(self, user_id: str, server_id: str) -> Optional[Dict]:
        """ユーザーデータを取得"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("""SELECT points, last_gacha_date 
                    FROM users 
                    WHERE user_id = ? AND server_id = ?""",
                 (user_id, server_id))
        result = c.fetchone()
        
        conn.close()
        if result:
            return {
                'points': result[0],
                'last_gacha_date': result[1]
            }
        return None

    def update_user_points(self, user_id: str, server_id: str, points: int, last_gacha_date: str):
        """ユーザーのポイントと最終ガチャ日を更新"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("""INSERT OR REPLACE INTO users (user_id, server_id, points, last_gacha_date)
                    VALUES (?, ?, ?, ?)""",
                 (user_id, server_id, points, last_gacha_date))
        
        conn.commit()
        conn.close()

    def get_server_ranking(self, server_id: str, limit: int = 10) -> List[Dict]:
        """サーバーのランキングを取得"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute("""SELECT user_id, points 
                    FROM users 
                    WHERE server_id = ? 
                    ORDER BY points DESC 
                    LIMIT ?""",
                 (server_id, limit))
        results = c.fetchall()
        
        conn.close()
        return [{'user_id': r[0], 'points': r[1]} for r in results]