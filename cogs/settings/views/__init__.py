# cogs/settings/views/__init__.py
from .base import BaseSettingsView
from .gacha_view import GachaSettingsView
from .battle_view import BattleSettingsView
from .fortunes_view import FortuneSettingsView
from .settings_view import SettingsView, FeatureSettingsView
from .point_consumption_view import PointConsumptionSettingsView  # 追加
from .token_view import TokenSettingsView

__all__ = [
    'BaseSettingsView',
    'GachaSettingsView',
    'BattleSettingsView',
    'FortuneSettingsView',
    'SettingsView',
    'FeatureSettingsView',
    'PointConsumptionSettingsView',
    'TokenSettingsView'  # 追加
    ]