import discord
from discord.ext import commands
import pytz
from datetime import datetime
import traceback
import random
import asyncio  # 追加
from utils.point_manager import PointSource

class GachaView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
    @discord.ui.button(label="ガチャを回す！", style=discord.ButtonStyle.primary)
    async def gacha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild_id)
            
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings or not settings.global_settings.features_enabled.get('gacha', True):
                await interaction.response.send_message(
                    "このサーバーではガチャ機能が無効になっています。",
                    ephemeral=True
                )
                return

            gacha_settings = settings.gacha_settings
            
            # 日付チェック
            jst = pytz.timezone('Asia/Tokyo')
            today = datetime.now(jst).strftime('%Y-%m-%d')
            
            # キャッシュからデータを取得
            cache_key = f"{user_id}_{server_id}_gacha_result"
            cached_data = self.bot.cache.get(cache_key)

            # 既にガチャを引いている場合の処理
            if cached_data and cached_data.get('last_gacha_date') == today:
                last_item = cached_data.get('last_item', '不明')
                last_points = cached_data.get('last_points', 0)
                # 合計ポイントは最新のものをDBから取得
                total_points = await self.bot.point_manager.get_points(server_id, user_id)
                print(f"[DEBUG] 今日のガチャは既に実行済みです - ユーザーID: {user_id}, 最後のアイテム: {last_item}, 獲得ポイント: {last_points}, 合計ポイント: {total_points}")

                embed = discord.Embed(title="今日のガチャ結果", color=0x00ff00)
                embed.add_field(name="獲得アイテム", value=last_item, inline=False)
                embed.add_field(
                    name="獲得ポイント", 
                    value=f"+{last_points}{settings.global_settings.point_unit}", 
                    inline=False
                )
                embed.add_field(
                    name="合計ポイント", 
                    value=f"{total_points}{settings.global_settings.point_unit}", 
                    inline=False
                )
                embed.set_footer(text="また明日挑戦してください！")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # アニメーション表示（ガチャ未実行の場合のみ）
            if gacha_settings.media and gacha_settings.media.gacha_animation_gif:
                animation_embed = discord.Embed(title="ガチャ実行中...", color=0x00ff00)
                animation_embed.set_image(url=gacha_settings.media.gacha_animation_gif)
                await interaction.response.send_message(embed=animation_embed, ephemeral=True)
                await asyncio.sleep(2)  # アニメーション表示時間
            else:
                # アニメーションがない場合は応答を遅延
                await interaction.response.defer(ephemeral=True)

            # ガチャ実行
            result_item = random.choices(
                gacha_settings.items,
                weights=[float(item['weight']) for item in gacha_settings.items]
            )[0]
            
            # 獲得ポイントを計算
            points_to_add = int(result_item['points'])
            print(f"[DEBUG] 獲得したポイント: {points_to_add}, アイテム: {result_item['name']}")

            # 現在のポイントを取得して新しいポイントを計算
            current_points = await self.bot.point_manager.get_points(server_id, user_id)
            new_points = current_points + points_to_add
            print(f"[DEBUG] 現在のポイント: {current_points}, 新しい合計ポイント: {new_points}")

            # キャッシュに結果を保存（その日のガチャ結果として）
            self.bot.cache[cache_key] = {
                'last_gacha_date': today,
                'last_item': result_item['name'],
                'last_points': points_to_add  # その日のガチャで獲得したポイント
            }

            # ポイントを更新（通知も行われる）
            await self.bot.point_manager.update_points(
                user_id,
                server_id,
                new_points,
                PointSource.GACHA
            )

            # ロール付与チェック
            if hasattr(gacha_settings, 'roles') and gacha_settings.roles:
                for role_setting in gacha_settings.roles:
                    if (role_setting.condition.type == 'points_threshold' and 
                        new_points >= role_setting.condition.value):
                        try:
                            role = discord.utils.get(interaction.guild.roles, id=int(role_setting.role_id))
                            if role and role not in interaction.user.roles:
                                await interaction.user.add_roles(role)
                                await interaction.followup.send(
                                    f"🎉 おめでとう！ {role.name} を獲得しました！",
                                    ephemeral=True
                                )
                        except Exception as e:
                            print(f"Failed to add role: {e}")

            # 結果表示用Embedの作成
            result_embed = await self._create_result_embed(
                result_item, points_to_add, new_points, settings, gacha_settings, interaction
            )
            print(f"[DEBUG] ガチャ結果Embedを作成: {result_embed.to_dict()}")

            if gacha_settings.media and gacha_settings.media.gacha_animation_gif:
                # アニメーション表示後、結果で上書き
                await interaction.edit_original_response(embed=result_embed)
            else:
                # 通常の結果表示
                await interaction.followup.send(embed=result_embed, ephemeral=True)
                
        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            await self._handle_error(interaction, "ガチャの実行中にエラーが発生しました。")

    async def _create_result_embed(self, result_item, points, new_points, settings, gacha_settings, interaction):
        """結果表示用Embedの作成"""
        print(f"[DEBUG] create_result_embed - ユーザーID: {interaction.user.id}")
        print(f"[DEBUG] create_result_embed - 獲得ポイント: {points}")
        print(f"[DEBUG] create_result_embed - 新しい合計ポイント: {new_points}")
        
        embed = discord.Embed(title="ガチャ結果", color=0x00ff00)
        embed.add_field(name="獲得アイテム", value=result_item['name'], inline=False)
        embed.add_field(
            name="獲得ポイント",
            value=f"+{points}{settings.global_settings.point_unit}",
            inline=False
        )
        embed.add_field(
            name="合計ポイント",
            value=f"{new_points}{settings.global_settings.point_unit}",
            inline=False
        )
        
        if gacha_settings.messages and gacha_settings.messages.win:
            # メッセージ内の変数を置換
            win_message = gacha_settings.messages.win.format(
                user=interaction.user.name,
                item=result_item['name']
            )
            embed.add_field(
                name="メッセージ",
                value=win_message,
                inline=False
            )
        
        if result_item.get('image_url'):
            embed.set_image(url=result_item['image_url'])
            
        return embed

    # GachaViewクラスに以下のメソッドを追加
    @discord.ui.button(label="ポイントを確認", style=discord.ButtonStyle.success)
    async def check_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild.id)
            
            print(f"[DEBUG] check_points - ユーザーID: {user_id}, サーバーID: {server_id}")

            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings:
                await interaction.response.send_message(
                    "設定の取得に失敗しました。",
                    ephemeral=True
                )
                return
            
            # ポイントを取得
            total_points = await self.bot.point_manager.get_points(server_id, user_id)
            print(f"[DEBUG] check_points - 取得したポイント: {total_points}")

            try:
                # サーバー内のランキングを取得
                server_rankings = await self.bot.db.get_server_user_rankings(server_id)
                server_active_users = len(server_rankings)
                user_server_rank = next(
                    (i + 1 for i, rank in enumerate(server_rankings) 
                    if str(rank['user_id']) == str(user_id)),
                    server_active_users + 1
                )

                embed = discord.Embed(title="ポイント状況", color=0x00ff00)
                embed.add_field(
                    name="現在のポイント", 
                    value=f"{total_points}{settings.global_settings.point_unit}", 
                    inline=False
                )
                embed.add_field(
                    name="ランキング", 
                    value=f"{user_server_rank}位/{server_active_users}人",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                print(f"Error in rankings: {str(e)}")
                # 最小限の情報だけでも表示
                embed = discord.Embed(title="ポイント状況", color=0x00ff00)
                embed.add_field(
                    name="現在のポイント", 
                    value=f"{total_points}{settings.global_settings.point_unit}", 
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            await self._handle_error(interaction, "ポイントの確認中にエラーが発生しました。")

        async def _handle_error(self, interaction: discord.Interaction, message: str):
            """エラーハンドリング"""
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(message, ephemeral=True)
                else:
                    await interaction.followup.send(message, ephemeral=True)
            except Exception:
                print("Failed to send error message to user")

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_setup(self, ctx):
        """ガチャの初期設定とパネルの設置"""
        server_id = str(ctx.guild.id)
        settings = await self.bot.get_server_settings(server_id)
        
        if not settings.global_settings.features_enabled.get('gacha', True):
            await ctx.send("このサーバーではガチャ機能が無効になっています。")
            return

        gacha_settings = settings.gacha_settings
        
        # セットアップメッセージ
        embed = await self._create_setup_embed(gacha_settings)
        await ctx.send(embed=embed)
        # セットアップ後にパネルを設置
        await self.gacha_panel(ctx)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gacha_panel(self, ctx):
        """ガチャパネルを設置"""
        settings = await self.bot.get_server_settings(str(ctx.guild.id))
        # print(f"[DEBUG] settings: {settings}")

        if not settings.global_settings.features_enabled.get('gacha', True):
            await ctx.send("このサーバーではガチャ機能が無効になっています。")
            return

        # 既存のパネルを削除
        try:
            async for message in ctx.channel.history(limit=50):
                if message.author == self.bot.user and message.embeds and len(message.embeds) > 0:
                    if message.embeds[0].title == "デイリーガチャ":
                        await message.delete()
        except Exception as e:
            print(f"Failed to delete old panel: {e}")

        gacha_settings = settings.gacha_settings
        # print(f"[DEBUG] gacha_settings: {gacha_settings}")

        # パネルの作成と送信
        embed = await self._create_panel_embed(gacha_settings)
        view = GachaView(self.bot)
        sent_message = await ctx.send(embed=embed, view=view)
        
        # 成功メッセージを送信
        success_embed = discord.Embed(
            title="セットアップ完了",
            description="ガチャパネルの設置が完了しました。",
            color=0x00ff00
        )
        temp_message = await ctx.send(embed=success_embed)
        
        # 3秒後に成功メッセージを削除
        await asyncio.sleep(3)
        try:
            await temp_message.delete()
        except:
            pass

    async def _create_setup_embed(self, settings):
        """セットアップ用Embedの作成"""
        setup_message = (settings.messages.setup 
                        if settings.messages and settings.messages.setup
                        else "**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！")
        
        embed = discord.Embed(
            title="ガチャセットアップ",
            description=setup_message,
            color=0x00ff00
        )
        
        if settings.media and settings.media.setup_image:
            embed.set_image(url=settings.media.setup_image)
            
        # 設定情報の追加
        # if settings.items:
        #     items_info = "\n".join([f"・{item['name']}" for item in settings.items])
        #     embed.add_field(
        #         name="設定済みアイテム",
        #         value=items_info,
        #         inline=False
        #     )
        
        return embed

    async def _create_panel_embed(self, settings):
        """パネル用Embedの作成"""
        daily_message = (settings.messages.daily 
                        if settings.messages and settings.messages.daily
                        else "1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。")

        embed = discord.Embed(
            title="デイリーガチャ",
            description=daily_message,
            color=0x00ff00
        )
        
        if settings.media and settings.media.banner_gif:
            embed.set_image(url=settings.media.banner_gif)
        
        # 現在のアイテム数とレアリティの表示
        # if settings.items:
        #     embed.add_field(
        #         name="ガチャ情報",
        #         value=f"アイテム総数: {len(settings.items)}種類",
        #         inline=False
        #     )
            
        return embed

async def setup(bot):
    await bot.add_cog(Gacha(bot))