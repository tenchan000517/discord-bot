import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime
import pytz
import traceback

DEFAULT_FORTUNE_RESULTS = {
    "大吉": {
        "description": "とても良い1日になりそう！チャレンジが実を結ぶ時です。",
        "color": 0xFF0000,
        "lucky_item": ["四つ葉のクローバー", "赤い靴下", "クリスタル"],
        "lucky_color": ["赤", "金", "白"],
        "weight": 10
    },
    "吉": {
        "description": "良いことが待っています。前向きな姿勢で過ごしましょう。",
        "color": 0xFFA500,
        "lucky_item": ["硬貨", "手帳", "鈴"],
        "lucky_color": ["青", "緑", "黄"],
        "weight": 30
    },
    "中吉": {
        "description": "平穏な一日になりそう。小さな幸せを大切に。",
        "color": 0xFFFF00,
        "lucky_item": ["ペン", "メモ帳", "キーホルダー"],
        "lucky_color": ["紫", "ピンク", "オレンジ"],
        "weight": 40
    },
    "小吉": {
        "description": "穏やかな日になりそう。慎重に行動すれば良い結果に。",
        "color": 0x00FF00,
        "lucky_item": ["消しゴム", "カレンダー", "マスク"],
        "lucky_color": ["水色", "茶色", "グレー"],
        "weight": 15
    },
    "凶": {
        "description": "少し慎重に行動した方が良さそう。でも心配はいりません。",
        "color": 0x808080,
        "lucky_item": ["お守り", "傘", "時計"],
        "lucky_color": ["黒", "紺", "深緑"],
        "weight": 5
    }
}

TRIGGER_WORDS = ["占い", "占って", "うらない"]

class Fortunes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_fortune_settings(self, guild_id: str):
        """占い設定を取得"""
        try:
            settings = await self.bot.get_server_settings(guild_id)
            if not settings or not settings.global_settings.features_enabled.get('fortune', True):
                return None
            return settings.fortune_settings
        except Exception as e:
            print(f"Error getting fortune settings: {e}")
            return None

    def get_fortune_results(self, settings):
        """設定に基づいた占い結果の定義を取得"""
        fortune_results = DEFAULT_FORTUNE_RESULTS.copy()
        
        # カスタムメッセージの適用
        if settings and hasattr(settings, 'custom_messages') and settings.custom_messages:
            for fortune_type, message in settings.custom_messages.items():
                if fortune_type in fortune_results:
                    fortune_results[fortune_type]['description'] = message

        return fortune_results

    async def perform_fortune(self, user, channel, guild):
        """占いを実行する共通関数"""
        try:
            user_id = str(user.id)
            server_id = str(guild.id)
            
            # 設定を取得
            settings = await self.get_fortune_settings(server_id)
            if settings is None:
                await channel.send("このサーバーでは占い機能が無効になっています。")
                return

            # 日付チェック
            jst = pytz.timezone('Asia/Tokyo')
            today = datetime.now(jst).strftime('%Y-%m-%d')
            
            # 最新の占い結果を取得
            latest_fortune = self.db.get_latest_fortune(user_id, server_id)
            
            if latest_fortune and latest_fortune['created_at'].split('T')[0] == today:
                daily_message = getattr(settings, 'daily_message', "今日はすでに占いをしています。明日また挑戦してください！")
                await channel.send(f"{user.mention} {daily_message}")
                return

            # 占い結果の取得
            fortune_results = self.get_fortune_results(settings)
            fortune_type = random.choices(
                list(fortune_results.keys()),
                weights=[f["weight"] for f in fortune_results.values()]
            )[0]
            fortune_data = fortune_results[fortune_type]

            # 結果を記録
            self.db.record_fortune(user_id, server_id, fortune_type)

            # 結果表示用Embedを作成
            embed = await self._create_fortune_embed(user, fortune_type, fortune_data)
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in perform_fortune: {e}")
            print(traceback.format_exc())
            await channel.send("占いの実行中にエラーが発生しました。")

    async def _create_fortune_embed(self, user, fortune_type, fortune_data):
        """占い結果表示用Embedの作成"""
        embed = discord.Embed(
            title=f"🔮 {user.name}さんの今日の運勢",
            color=fortune_data["color"]
        )
        
        embed.add_field(
            name=f"**{fortune_type}**",
            value=fortune_data["description"],
            inline=False
        )
        
        lucky_item = random.choice(fortune_data["lucky_item"])
        lucky_color = random.choice(fortune_data["lucky_color"])
        
        embed.add_field(name="ラッキーアイテム", value=lucky_item, inline=True)
        embed.add_field(name="ラッキーカラー", value=lucky_color, inline=True)
        
        embed.set_footer(text="毎日0時にリセットされます")
        
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        if any(word in message.content for word in TRIGGER_WORDS):
            await self.perform_fortune(message.author, message.channel, message.guild)

    @app_commands.command(name="fortune_stats", description="占い結果の統計を表示します")
    async def fortune_stats(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild_id)
            
            # 設定を確認
            settings = await self.get_fortune_settings(server_id)
            if settings is None:
                await interaction.response.send_message(
                    "このサーバーでは占い機能が無効になっています。",
                    ephemeral=True
                )
                return
            
            # 履歴の取得と統計の作成
            stats_embed = await self._create_stats_embed(user_id, server_id, interaction.user.name)
            await interaction.response.send_message(embed=stats_embed, ephemeral=True)

        except Exception as e:
            print(f"Error in fortune_stats: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "統計情報の取得中にエラーが発生しました。",
                ephemeral=True
            )

    async def _create_stats_embed(self, user_id, server_id, username):
        """統計情報表示用Embedの作成"""
        history = self.db.get_fortune_history_stats(user_id, server_id)
        
        if not history:
            return discord.Embed(
                title=f"🔮 {username}さんの運勢統計",
                description="まだ占い履歴がありません。チャットで「占い」と発言してみましょう！",
                color=0x00ff00
            )
            
        embed = discord.Embed(
            title=f"🔮 {username}さんの運勢統計",
            color=0x00ff00
        )
        
        # 結果の集計
        fortune_counts = {}
        for fortune_type in DEFAULT_FORTUNE_RESULTS.keys():
            count = sum(1 for record in history if record["fortune_type"] == fortune_type)
            if count > 0:
                fortune_counts[fortune_type] = count
        
        # 合計回数を計算
        total_count = sum(fortune_counts.values())
        
        # 結果を表示
        for fortune_type, count in fortune_counts.items():
            percentage = (count / total_count) * 100
            embed.add_field(
                name=fortune_type,
                value=f"{count}回 ({percentage:.1f}%)",
                inline=True
            )
                
        embed.set_footer(text=f"総占い回数: {total_count}回")
        return embed

async def setup(bot):
    await bot.add_cog(Fortunes(bot))