# models/rewards.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, List
import uuid

@dataclass
class Reward:
    id: str
    user_id: str
    server_id: str
    points_spent: int
    reward_type: str  # 'COUPON', 'NFT', 'TOKEN'
    claim_code: str   # クーポンコード、トランザクションハッシュなど
    created_at: datetime
    claimed_at: Optional[datetime]
    status: str      # 'PENDING', 'COMPLETED', 'FAILED'
    metadata: Dict   # 追加情報

    @classmethod
    def create(cls, user_id: str, server_id: str, points: int, reward_type: str):
        """新しい報酬インスタンスを作成"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            server_id=server_id,
            points_spent=points,
            reward_type=reward_type,
            claim_code="",
            created_at=datetime.now(),
            claimed_at=None,
            status="PENDING",
            metadata={}
        )

    def to_dict(self) -> Dict:
        """DynamoDBに保存可能な形式に変換"""
        data = asdict(self)
        # datetime型をISO形式の文字列に変換
        data['created_at'] = self.created_at.isoformat()
        if self.claimed_at:
            data['claimed_at'] = self.claimed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Reward':
        """DynamoDBのデータからインスタンスを作成"""
        # 文字列の日付をdatetime型に変換
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('claimed_at'):
            data['claimed_at'] = datetime.fromisoformat(data['claimed_at'])
        return cls(**data)