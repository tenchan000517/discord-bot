from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class BattleStatus(Enum):
    WAITING = "waiting"
    COUNTDOWN = "countdown"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class EventType(Enum):
    BATTLE = "battle"
    ACCIDENT = "accident"
    ITEM = "item"
    REVIVAL = "revival"
    RANDOM = "random"

@dataclass
class BattleEvent:
    event_type: EventType
    message: str
    killed_players: List[str] = None
    revived_players: List[str] = None
    item_receivers: List[str] = None

@dataclass
class BattleResults:
    winner: str
    runners_up: List[str]  # 2位～5位
    kill_counts: Dict[str, int]  # プレイヤーID: キル数
    revival_counts: Dict[str, int]  # プレイヤーID: 復活回数

@dataclass
class BattleSettings:
    required_role_id: Optional[str]  # 必要なロールID（Noneの場合は制限なし）
    winner_role_id: Optional[str]  # 勝者に付与するロールID
    points_enabled: bool  # ポイント付与システムの有効/無効
    points_per_kill: int  # 1キルあたりのポイント
    winner_points: int  # 優勝賞金
    start_delay_minutes: int = 2  # 開始までの待機時間（分）
    test_mode: bool = False  # テストモードフラグ
    dummy_count: int = 10  # テストモード時のダミープレイヤー数

@dataclass
class BattleGame:
    server_id: str
    status: BattleStatus
    settings: BattleSettings
    players: List[str]  # 参加プレイヤーのID
    alive_players: List[str]  # 生存プレイヤーのID
    dead_players: List[str]  # 死亡プレイヤーのID
    kill_counts: Dict[str, int]  # キル数カウント
    revival_counts: Dict[str, int]  # 復活回数カウント
    start_time: datetime
    round_number: int = 1

    def add_player(self, player_id: str) -> bool:
        """プレイヤーを追加"""
        if player_id in self.players:
            return False
        self.players.append(player_id)
        self.alive_players.append(player_id)
        self.kill_counts[player_id] = 0
        self.revival_counts[player_id] = 0
        return True

    def remove_player(self, player_id: str) -> bool:
        """プレイヤーを削除（ゲーム開始前のみ）"""
        if self.status != BattleStatus.WAITING:
            return False
        if player_id in self.players:
            self.players.remove(player_id)
            self.alive_players.remove(player_id)
            return True
        return False

    def kill_player(self, player_id: str, killer_id: Optional[str] = None) -> bool:
        """プレイヤーを殺害"""
        if player_id in self.alive_players:
            self.alive_players.remove(player_id)
            self.dead_players.append(player_id)
            if killer_id:
                self.kill_counts[killer_id] = self.kill_counts.get(killer_id, 0) + 1
            return True
        return False

    def revive_player(self, player_id: str) -> bool:
        """プレイヤーを復活"""
        if player_id in self.dead_players:
            self.dead_players.remove(player_id)
            self.alive_players.append(player_id)
            self.revival_counts[player_id] = self.revival_counts.get(player_id, 0) + 1
            return True
        return False

    @property
    def is_finished(self) -> bool:
        """ゲーム終了判定"""
        return len(self.alive_players) <= 1

    def get_results(self) -> BattleResults:
        """ゲーム結果を取得"""
        if not self.is_finished:
            return None
            
        winner = self.alive_players[0] if self.alive_players else None
        # 最後に死亡した順に上位入賞者を決定
        runners_up = self.dead_players[-4:] if len(self.dead_players) >= 4 else self.dead_players[:]
        runners_up.reverse()  # 2位から順に並べ替え
        
        return BattleResults(
            winner=winner,
            runners_up=runners_up,
            kill_counts=self.kill_counts,
            revival_counts=self.revival_counts
        )