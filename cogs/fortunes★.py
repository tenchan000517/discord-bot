import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime
import pytz

FORTUNE_RESULTS = {
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

    async def perform_fortune(self, user, channel, guild):
        """占いを実行する共通関数"""
        user_id = str(user.id)
        server_id = str(guild.id)
        
        # 日付チェック
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).strftime('%Y-%m-%d')
        
        # 最新の占い結果を取得
        latest_fortune = self.db.get_latest_fortune(user_id, server_id)
        
        if latest_fortune and latest_fortune['created_at'].split('T')[0] == today:
            await channel.send(
                f"{user.mention} 今日はすでに占いをしています。明日また挑戦してください！"
            )
            return

        # 運勢を決定
        fortune_type = random.choices(
            list(FORTUNE_RESULTS.keys()),
            weights=[f["weight"] for f in FORTUNE_RESULTS.values()]
        )[0]
        fortune_data = FORTUNE_RESULTS[fortune_type]

        # 結果を記録
        self.db.record_fortune(user_id, server_id, fortune_type)

        # 結果表示用Embedを作成
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
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # ボットのメッセージは無視
        if message.author.bot:
            return
            
        # DMは無視
        if not message.guild:
            return
            
        # メッセージ内容をチェック
        if any(word in message.content for word in TRIGGER_WORDS):
            await self.perform_fortune(message.author, message.channel, message.guild)

    @app_commands.command(name="fortune_stats", description="占い結果の統計を表示します")
    async def fortune_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild_id)
        
        # ユーザーの占い履歴を取得
        history = self.db.get_fortune_history_stats(user_id, server_id)
        
        if not history:
            await interaction.response.send_message(
                "まだ占い履歴がありません。チャットで「占い」と発言してみましょう！",
                ephemeral=True
            )
            return
            
        embed = discord.Embed(
            title=f"🔮 {interaction.user.name}さんの運勢統計",
            color=0x00ff00
        )
        
        # 結果の集計
        fortune_counts = {}
        for fortune_type in FORTUNE_RESULTS.keys():
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
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fortunes(bot))