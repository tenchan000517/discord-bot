import discord
from discord.ext import commands
import json
import pytz
from datetime import datetime
import csv
from io import StringIO
import traceback  # 追加

class GachaView(discord.ui.View):
    def __init__(self, db):
        super().__init__(timeout=None)
        self.db = db
    
    @discord.ui.button(label="ガチャを回す！", style=discord.ButtonStyle.primary, custom_id="gacha_button")
    async def gacha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild_id)
            
            print(f"Gacha button pressed by user {user_id} in server {server_id}")  # デバッグ用
            
            settings = self.db.get_server_settings(server_id)
            print(f"Server settings: {settings}")  # デバッグ用
            
            if not settings:
                await interaction.response.send_message("ガチャが設定されていません。", ephemeral=True)
                return

            jst = pytz.timezone('Asia/Tokyo')
            today = datetime.now(jst).strftime('%Y-%m-%d')
            
            user_data = self.db.get_user_data(user_id, server_id)
            print(f"User data: {user_data}")  # デバッグ用
            
            if user_data and user_data.get('last_gacha_date') == today:
                await interaction.response.send_message("今日はすでにガチャを回しています。明日また挑戦してください！", ephemeral=True)
                return
                
            # ガチャ実行
            import random
            items = settings['settings']['items']  # 修正: settingsの階層構造に対応
            print(f"Available items: {items}")  # デバッグ用
            
            result_item = random.choices(items, weights=[float(item['weight']) for item in items])[0]  # Decimalを float に変換
            points = int(float(result_item['points']))  # Decimalを int に変換
            
            # ポイント更新
            current_points = user_data.get('points', 0) if user_data else 0
            new_points = current_points + points
            update_result = self.db.update_user_points(user_id, server_id, new_points, today)
            print(f"Points update result: {update_result}")  # デバッグ用
            
            # ロール付与チェック
            role_levels = [
                (10, "初級ロール"),
                (20, "中級ロール"),
                (30, "上級ロール"),
            ]
            
            for point_req, role_name in role_levels:
                if new_points >= point_req:
                    role = discord.utils.get(interaction.guild.roles, name=role_name)
                    if role and role not in interaction.user.roles:
                        await interaction.user.add_roles(role)
                        await interaction.followup.send(f"🎉 おめでとう！ {role_name} を獲得しました！", ephemeral=True)

            # 結果表示
            embed = discord.Embed(title="ガチャ結果", color=0x00ff00)
            embed.add_field(name="獲得アイテム", value=result_item['name'], inline=False)
            embed.add_field(name="獲得ポイント", value=f"+{points}ポイント", inline=False)
            embed.add_field(name="合計ポイント", value=f"{new_points}ポイント", inline=False)
            embed.add_field(
                name="結果をシェアしよう！",
                value="ぜひ結果をX (twitter)に投稿してね！ #あなたのサーバー名 #ガチャ",
                inline=False
            )
            
            if result_item.get('image_url'):
                embed.set_image(url=result_item['image_url'])
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # コンソールにエラーを出力
            try:
                await interaction.response.send_message("ガチャの実行中にエラーが発生しました。", ephemeral=True)
            except:
                try:
                    await interaction.followup.send("ガチャの実行中にエラーが発生しました。", ephemeral=True)
                except:
                    print("Failed to send error message to user")

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_setup(self, ctx):
        """ガチャの初期設定"""
        server_id = str(ctx.guild.id)
        
        # デフォルト設定
        default_settings = {
            'items': [
                {
                    'name': 'SSRアイテム',
                    'weight': 5,
                    'points': 100,
                    'image_url': ''
                },
                {
                    'name': 'SRアイテム',
                    'weight': 15,
                    'points': 50,
                    'image_url': ''
                },
                {
                    'name': 'Rアイテム',
                    'weight': 30,
                    'points': 30,
                    'image_url': ''
                },
                {
                    'name': 'Nアイテム',
                    'weight': 50,
                    'points': 10,
                    'image_url': ''
                }
            ]
        }
        
        self.db.update_server_settings(server_id, default_settings)
        
        # 初期設定メッセージ
        embed = discord.Embed(
            title="**ガチャを回して運試し！**",
            description=(
                "1日1回ガチャが回せるよ！\n"
                "ぜひ結果をX (twitter)に投稿してね！\n"
                "ガチャを回してポイントを貯めよう！\n\n"
                "１０P貯める毎に、自動で『』ロールが１つ付与されるよ！\n"
                "『』ロールを獲得すると、運営から『』ロールを付与するよ！\n"
                "待っててね！ ⇄ ３００AP\n"
                "※AP=ｴｲﾘｱﾝﾎﾟｲﾝﾄ"
            ),
            color=0x00ff00
        )
        
        await ctx.send(embed=embed)
        await self.gacha_panel(ctx)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_panel(self, ctx):
        """ガチャパネルを設置"""
        embed = discord.Embed(
            title="デイリーガチャ",
            description="1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。",
            color=0x00ff00
        )
        
        view = GachaView(self.db)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def import_points(self, ctx):
        """ポイントをCSVからインポート"""
        if not ctx.message.attachments:
            await ctx.send("CSVファイルを添付してください。")
            return

        try:
            attachment = ctx.message.attachments[0]
            csv_content = await attachment.read()
            csv_text = csv_content.decode('utf-8')
            
            reader = csv.DictReader(StringIO(csv_text))
            updated_count = 0
            
            for row in reader:
                user_id = row['user_id']
                points = int(row['points'])
                self.db.update_user_points(user_id, str(ctx.guild.id), points, None)
                updated_count += 1

            await ctx.send(f"{updated_count}人のポイントを更新しました。")

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {str(e)}")

async def setup(bot):
    await bot.add_cog(Gacha(bot))