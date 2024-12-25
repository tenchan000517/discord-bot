from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pytz
from enum import Enum
import uuid

class ConditionType(Enum):
    POINTS_THRESHOLD = "points_threshold"
    POINTS_RANGE = "points_range"
    MESSAGE_COUNT = "message_count"
    REACTION_COUNT = "reaction_count"
    TIME_CONDITION = "time_condition"

class ActionType(Enum):
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    SEND_MESSAGE = "send_message"
    GIVE_POINTS = "give_points"
    SEND_NOTIFICATION = "send_notification"  # 追加

class OperatorType(Enum):
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"

@dataclass
class Condition:
    type: ConditionType
    operator: OperatorType
    value: Union[int, str, List[Union[int, str]]]
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'operator': self.operator.value,
            'value': self.value,
            'parameters': self.parameters or {}
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Condition':
        return cls(
            type=ConditionType(data['type']),
            operator=OperatorType(data['operator']),
            value=data['value'],
            parameters=data.get('parameters', {})
        )
    
@dataclass
class NotificationSettings:
    enabled: bool
    channel_id: str
    message_template: str

    @classmethod
    def from_dict(cls, data: dict) -> 'NotificationSettings':
        print(f"[DEBUG] NotificationSettings.from_dict input: {data}")
        return cls(
            enabled=data.get('enabled', False),
            channel_id=data.get('channelId', ''),  # 'channelId' に対応
            message_template=data.get('messageTemplate', '{user_mention}\nおめでとうございます！{role_name}を獲得しました！🎉')
        )


@dataclass
class Action:
    type: ActionType
    value: Union[str, int, Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None
    notification_settings: Optional[NotificationSettings] = None

    def to_dict(self) -> dict:
        data = {
            'type': self.type.value,
            'value': self.value,
            'parameters': self.parameters or {},
            'notification_settings': self.notification_settings.to_dict() 
                if self.notification_settings else None
        }
        print(f"[DEBUG] Action to_dict output: {data}")  # print文をreturnの前に移動
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Action':
        print(f"[DEBUG] Action.from_dict input: {data}")
        
        # notification_settings を作成
        notification_settings = None
        # ルートレベルの notification を確認
        if 'notification' in data:
            print(f"[DEBUG] Found notification settings in action data")
            notification_settings = NotificationSettings.from_dict(data['notification'])
        # parameters 内の notification を確認（既存の設定を保持）
        elif 'parameters' in data and 'notification' in data['parameters']:
            print(f"[DEBUG] Found notification settings in parameters")
            notification_settings = NotificationSettings.from_dict(data['parameters']['notification'])
        else:
            print(f"[DEBUG] No notification settings found")

        action = cls(
            type=ActionType(data['type']),
            value=data['value'],
            parameters=data.get('parameters', {}),
            notification_settings=notification_settings
        )
        print(f"[DEBUG] Created action with notification_settings: {notification_settings}")
        return action

@dataclass
class AutomationRule:
    id: str
    server_id: str
    name: str
    description: str
    enabled: bool
    conditions: List[Condition]
    actions: List[Action]
    cooldown: Optional[int] = None  # minutes
    last_triggered: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    notification: Optional[Dict[str, Any]] = None  # notification 属性を追加

    def __post_init__(self):
        now = datetime.now(pytz.UTC).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'conditions': [c.to_dict() for c in self.conditions],
            'actions': [a.to_dict() for a in self.actions],
            'cooldown': self.cooldown,
            'last_triggered': self.last_triggered,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'notification': self.notification  # notification を追加
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AutomationRule':
        print(f"[DEBUG] AutomationRule.from_dict input: {data}")
        
        # 各アクションに通知設定を追加
        actions_data = data['actions']
        if 'notification' in data:
            # 各アクションデータに通知設定を追加
            actions_data = [{**action, 'notification': data['notification']} 
                        for action in actions_data]
        
        actions = [Action.from_dict(a) for a in actions_data]
        
        return cls(
            id=data['id'],
            server_id=data['server_id'],
            name=data['name'],
            description=data['description'],
            enabled=data['enabled'],
            conditions=[Condition.from_dict(c) for c in data['conditions']],
            actions=actions,
            cooldown=data.get('cooldown'),
            last_triggered=data.get('last_triggered'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            notification=data.get('notification')
        )

    @classmethod
    def create_new(cls, server_id: str, name: str, description: str) -> 'AutomationRule':
        return cls(
            id=str(uuid.uuid4()),
            server_id=server_id,
            name=name,
            description=description,
            enabled=True,
            conditions=[],
            actions=[]
        )