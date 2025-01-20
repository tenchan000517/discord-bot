# contracts/wallet_connect.py
from web3 import Web3
# 古いミドルウェアのimportを削除し、新しい方法を使用
from eth_account import Account
import asyncio
import json
import qrcode
import io
from typing import Optional, Dict, Tuple
import logging
from web3.types import TxParams

logger = logging.getLogger(__name__)

class WalletConnectManager:
    def __init__(self):
        self.sessions: Dict[str, "WalletSession"] = {}

    async def create_session(self, user_id: str) -> Tuple[str, bytes]:
        """新規セッション作成"""
        try:
            session_id = f"session_{user_id}_{asyncio.get_event_loop().time()}"
            
            # QRコード生成
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # セッション情報を追加
            connection_data = {
                "session": session_id,
                "user": user_id
            }
            qr.add_data(json.dumps(connection_data))
            qr.make(fit=True)
            
            # QRコードを画像として取得（バイナリとして扱う）
            img = qr.make_image(fill_color="black", back_color="white")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            
            # セッション作成
            self.sessions[user_id] = WalletSession(
                session_id=session_id,
                user_id=user_id
            )
            
            # バイナリデータとして返す
            return session_id, img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def handle_connection(self, user_id: str, timeout: int = 120) -> Optional[str]:
        """接続処理を待機"""
        try:
            session = self.sessions.get(user_id)
            if not session:
                return None
                
            # タイムアウトまでウォレット接続を待機
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                if session.connected and session.accounts:
                    return session.accounts[0]
                await asyncio.sleep(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
            return None

    def is_connected(self, user_id: str) -> bool:
        """接続状態を確認"""
        session = self.sessions.get(user_id)
        return session is not None and session.connected

    async def get_active_session(self, user_id: str) -> Optional["WalletSession"]:
        """アクティブなセッションを取得"""
        session = self.sessions.get(user_id)
        if session and session.connected:
            return session
        return None

    async def disconnect(self, user_id: str) -> bool:
        """セッションを切断"""
        try:
            if user_id in self.sessions:
                self.sessions.pop(user_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error disconnecting session: {e}")
            return False

class WalletSession:
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.connected = False
        self.accounts: list[str] = []
        self.connected_at = None
        self.private_key: Optional[str] = None  # 必要な場合のみ使用