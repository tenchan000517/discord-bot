import random
from typing import List, Optional
import discord
from models.battle import EventType, BattleEvent

# メッセージテンプレートは変更なし
KILL_MESSAGES = [
    "{killer}は{victim}の膝を粉砕し、死体は後に野生動物に食べられた。",
    "{killer}は{victim}を倒した。「これでおしまいだ！」",
    "{killer}は{victim}を崖から突き落として背骨を折った。",
    "{killer}は棒切れで{victim}を倒した。なんと野蛮な...。",
    "{killer}は{victim}の心臓を狙い撃ちにした。「スポンサーからの依頼だ。」",
    "{killer}は寝ている{victim}を背後から襲った！不運な展開だ。",
]

ACCIDENT_MESSAGES = [
    "{victim}は高所から転落した。",
    "{victim}は毒のある木の実を食べてしまった。",
    "{victim}は予防可能な原因で死亡した。",
    "{victim}は笑いすぎて死んでしまった。",
    "{victim}は木から落ちて死亡。",
    "{victim}は食中毒で死亡！不運だ。",
]

ITEM_MESSAGES = [
    "{player}は死体からダガーを見つけた。",
    "{player}は弓を見つけた。",
    "{player}は食料パッケージを発見した。",
    "{player}は鋭い刃物を手に入れた。",
    "{player}は骨から短剣を作り出した！",
]

RANDOM_MESSAGES = [
    "{player}はチューリップの中を忍び足で進んだ。",
    "{player}は近くで誰かが歩く音を聞いた。",
    "{player}は食べられる木の実を見つけた。",
    "{player}は湖を見つけ、キャンプを設営することにした。",
]

REVIVAL_MESSAGES = [
    "{player}は神によって復活した。",
    "{player}は死を偽装していた。サプライズだ！",
    "{player}は戦いに復帰した。",
]

def format_player_name(player_id: str) -> str:
    """プレイヤー名を整形"""
    if player_id.startswith('dummy_'):
        return f"ダミープレイヤー {player_id}"
    return f"<@{player_id}>"

def generate_battle_event(alive_players: List[str], dead_players: List[str]) -> Optional[BattleEvent]:
    """ランダムなバトルイベントを生成"""
    if len(alive_players) < 2:
        return None

    event_type = random.choices(
        [EventType.BATTLE, EventType.ACCIDENT, EventType.ITEM, EventType.RANDOM, EventType.REVIVAL],
        weights=[0.4, 0.2, 0.2, 0.15, 0.05]
    )[0]

    if event_type == EventType.BATTLE:
        killer, victim = random.sample(alive_players, 2)
        message = random.choice(KILL_MESSAGES).format(
            killer=format_player_name(killer),
            victim=format_player_name(victim)
        )
        return BattleEvent(
            event_type=event_type,  # typeをevent_typeに変更
            message=message,
            killed_players=[victim]
        )

    elif event_type == EventType.ACCIDENT:
        victim = random.choice(alive_players)
        message = random.choice(ACCIDENT_MESSAGES).format(
            victim=format_player_name(victim)
        )
        return BattleEvent(
            event_type=event_type,  # typeをevent_typeに変更
            message=message,
            killed_players=[victim]
        )

    elif event_type == EventType.ITEM:
        player = random.choice(alive_players)
        message = random.choice(ITEM_MESSAGES).format(
            player=format_player_name(player)
        )
        return BattleEvent(
            event_type=event_type,  # typeをevent_typeに変更
            message=message,
            item_receivers=[player]
        )

    elif event_type == EventType.RANDOM:
        player = random.choice(alive_players)
        message = random.choice(RANDOM_MESSAGES).format(
            player=format_player_name(player)
        )
        return BattleEvent(
            event_type=event_type,  # typeをevent_typeに変更
            message=message
        )

    elif event_type == EventType.REVIVAL and dead_players:
        player = random.choice(dead_players)
        message = random.choice(REVIVAL_MESSAGES).format(
            player=format_player_name(player)
        )
        return BattleEvent(
            event_type=event_type,  # すでに正しい
            message=message,
            revived_players=[player]
        )

    return None

def format_round_message(round_number: int, events: List[BattleEvent], players_left: int) -> discord.Embed:
    """ラウンドメッセージを埋め込みとして整形"""
    embed = discord.Embed(
        title=f"⚔️ ラウンド {round_number}",
        color=discord.Color.blue()
    )

    # イベントメッセージを埋め込みの説明として追加
    event_messages = []
    for event in events:
        if event:
            # イベントタイプに応じてアイコンを追加
            icon = {
                EventType.BATTLE: "💀",
                EventType.ACCIDENT: "☠️",
                EventType.ITEM: "🎁",
                EventType.RANDOM: "👣",
                EventType.REVIVAL: "✨"
            }.get(event.type, "📢")
            
            event_messages.append(f"{icon} {event.message}")

    if event_messages:
        embed.description = "\n".join(event_messages)
    else:
        embed.description = "このラウンドは特に何も起こりませんでした..."

    # 生存者数を埋め込みのフィールドとして追加
    embed.add_field(
        name="生存者",
        value=f"👥 残り {players_left}人",
        inline=False
    )

    return embed