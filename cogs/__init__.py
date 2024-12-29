# cogs/__init__.py
from .admin import Admin
from .battle import BattleRoyale
from .fortunes import Fortunes
from .gacha import Gacha
from .automation import Automation  # 追加
from .points_consumption import PointsConsumption  # 追加

__all__ = [
    'Admin',
    'BattleRoyale',
    'Fortunes',
    'Gacha',
    'Automation',
    'PointsConsumption'  # 追加
]