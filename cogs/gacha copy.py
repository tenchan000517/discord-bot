# cogs/gacha.py
import discord
from discord.ext import commands
import pytz
from datetime import datetime
import traceback

class GachaView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="ガチャを回す！", style=discord.ButtonStyle.primary, custom_id="gacha_button")
    async def gacha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild_id)
            
            # サーバー設定を取得
            server_settings = await self.bot.get_server_settings(server_id)
            if not server_settings or not server_settings.global_settings.features_enabled.get('gacha', True):
                await interaction.response.send_message(
                    "このサーバーではガチャ機能が無効になっています。",
                    ephemeral=True
                )
                return

            gacha_settings = server_settings.gacha_settings
            if not gacha_settings or not gacha_settings.items:
                await interaction.response.send_message(
                    "ガチャが設定されていません。",
                    ephemeral=True
                )
                return

            # 日付チェック
            jst = pytz.timezone('Asia/Tokyo')
            today = datetime.now(jst).strftime('%Y-%m-%d')
            
            user_data = self.bot.db.get_user_data(user_id, server_id)
            if user_data and user_data.get('last_gacha_date') == today:
                daily_message = (gacha_settings.messages.daily 
                               if gacha_settings.messages and gacha_settings.messages.daily
                               else "今日はすでにガチャを回しています。明日また挑戦してください！")
                await interaction.response.send_message(daily_message, ephemeral=True)
                return
                
            # ガチャ実行
            import random
            items = gacha_settings.items
            result_item = random.choices(items, weights=[float(item['weight']) for item in items])[0]
            points = int(float(result_item['points']))
            
            # ポイント更新
            current_points = user_data.get('points', 0) if user_data else 0
            new_points = current_points + points
            update_result = self.bot.db.update_user_points(user_id, server_id, new_points, today)
            
            # ロール付与チェック
            if gacha_settings.roles:
                for role_setting in gacha_settings.roles:
                    if (role_setting.condition.type == 'points_threshold' and 
                        new_points >= role_setting.condition.value):
                        role = discord.utils.get(interaction.guild.roles, id=int(role_setting.role_id))
                        if role and role not in interaction.user.roles:
                            await interaction.user.add_roles(role)
                            await interaction.followup.send(
                                f"🎉 おめでとう！ {role.name} を獲得しました！",
                                ephemeral=True
                            )

            # 結果表示
            embed = discord.Embed(title="ガチャ結果", color=0x00ff00)
            embed.add_field(name="獲得アイテム", value=result_item['name'], inline=False)
            embed.add_field(
                name="獲得ポイント",
                value=f"+{points}{server_settings.global_settings.point_unit}",
                inline=False
            )
            embed.add_field(
                name="合計ポイント",
                value=f"{new_points}{server_settings.global_settings.point_unit}",
                inline=False
            )
            
            # カスタムメッセージがある場合は追加
            if gacha_settings.messages and gacha_settings.messages.win:
                embed.add_field(
                    name="メッセージ",
                    value=gacha_settings.messages.win,
                    inline=False
                )
            else:
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
            print(error_msg)
            try:
                await interaction.response.send_message(
                    "ガチャの実行中にエラーが発生しました。",
                    ephemeral=True
                )
            except:
                try:
                    await interaction.followup.send(
                        "ガチャの実行中にエラーが発生しました。",
                        ephemeral=True
                    )
                except:
                    print("Failed to send error message to user")

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_setup(self, ctx):
        """ガチャの初期設定"""
        server_id = str(ctx.guild.id)
        settings = await self.bot.get_server_settings(server_id)
        
        if not settings.global_settings.features_enabled.get('gacha', True):
            await ctx.send("このサーバーではガチャ機能が無効になっています。")
            return

        gacha_settings = settings.gacha_settings
        
        # セットアップメッセージの取得
        setup_message = (gacha_settings.messages.setup 
                        if gacha_settings.messages and gacha_settings.messages.setup
                        else "**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！")
        
        # 初期設定メッセージ
        embed = discord.Embed(
            title=setup_message,
            color=0x00ff00
        )
        
        if gacha_settings.media and gacha_settings.media.setup_image:
            embed.set_image(url=gacha_settings.media.setup_image)
        
        await ctx.send(embed=embed)
        await self.gacha_panel(ctx)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_panel(self, ctx):
        """ガチャパネルを設置"""
        settings = await self.bot.get_server_settings(str(ctx.guild.id))
        if not settings.global_settings.features_enabled.get('gacha', True):
            await ctx.send("このサーバーではガチャ機能が無効になっています。")
            return

        gacha_settings = settings.gacha_settings
        daily_message = (gacha_settings.messages.daily 
                        if gacha_settings.messages and gacha_settings.messages.daily
                        else "1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。")

        embed = discord.Embed(
            title="デイリーガチャ",
            description=daily_message,
            color=0x00ff00
        )
        
        if gacha_settings.media and gacha_settings.media.banner_gif:
            embed.set_image(url=gacha_settings.media.banner_gif)
        
        view = GachaView(self.bot)
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
            
            server_settings = await self.bot.get_server_settings(str(ctx.guild.id))
            point_unit = server_settings.global_settings.point_unit
            
            for row in reader:
                user_id = row['user_id']
                points = int(row['points'])
                self.bot.db.update_user_points(user_id, str(ctx.guild.id), points, None)
                updated_count += 1

            await ctx.send(f"{updated_count}人の{point_unit}を更新しました。")

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {str(e)}")

async def setup(bot):
    await bot.add_cog(Gacha(bot))