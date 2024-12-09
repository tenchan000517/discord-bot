from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class TeamColor(Enum):
    RED = "red"
    BLUE = "blue"

class RumbleStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

@dataclass
class RumbleMatch:
    server_id: str
    status: RumbleStatus
    players: Dict[str, TeamColor]  # {user_id: team}
    ready_players: List[str]  # ready状態のuser_id一覧
    
    @property
    def can_start(self) -> bool:
        """ゲーム開始可能か確認"""
        if self.status != RumbleStatus.WAITING:
            return False
            
        # 最小2人、各チーム同数確認
        red_team = sum(1 for team in self.players.values() if team == TeamColor.RED)
        blue_team = sum(1 for team in self.players.values() if team == TeamColor.BLUE)
        if red_team < 1 or red_team != blue_team:
            return False
            
        # 全員ready確認
        return all(player_id in self.ready_players for player_id in self.players.keys())

    def add_player(self, user_id: str) -> bool:
        """プレイヤーを追加"""
        if user_id in self.players:
            return False
            
        # チーム振り分け（人数が少ないチームに割り当て）
        red_count = sum(1 for t in self.players.values() if t == TeamColor.RED)
        blue_count = sum(1 for t in self.players.values() if t == TeamColor.BLUE)
        
        team = TeamColor.RED if red_count <= blue_count else TeamColor.BLUE
        self.players[user_id] = team
        return True
        
    def remove_player(self, user_id: str) -> bool:
        """プレイヤーを削除"""
        if user_id in self.ready_players:
            self.ready_players.remove(user_id)
        return bool(self.players.pop(user_id, None))
        
    def toggle_ready(self, user_id: str) -> bool:
        """準備状態を切り替え"""
        if user_id not in self.players:
            return False
            
        if user_id in self.ready_players:
            self.ready_players.remove(user_id)
        else:
            self.ready_players.append(user_id)
        return True