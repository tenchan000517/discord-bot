import discord
from discord.ext import commands
from discord import app_commands
import pytz
from datetime import datetime
import traceback
import random
import asyncio  # 追加
from utils.point_manager import PointSource
import urllib.parse  # 追加
from typing import Optional  # 追加
from models.server_settings import GachaSettings, MessageSettings, MediaSettings, GachaFeatureSettings
import uuid
from discord.ext import tasks
from datetime import time as datetime_time

class GachaView(discord.ui.View):
    def __init__(self, bot, gacha_id: str):  # gacha_idを追加
        super().__init__(timeout=None)
        self.bot = bot
        self.gacha_id = gacha_id  # インスタンス変数として保存
        # 今日のガチャ結果メッセージを追跡する辞書を追加
        if not hasattr(bot, 'gacha_messages'):
            bot.gacha_messages = {}

    async def _create_result_embed(self, result_item, points, new_points, settings, gacha_settings, interaction, point_unit_id="1"):
            """結果表示用Embedの作成"""
            print(f"[DEBUG] create_result_embed - ユーザーID: {interaction.user.id}")
            print(f"[DEBUG] create_result_embed - 獲得ポイント: {points}")
            print(f"[DEBUG] create_result_embed - 新しい合計ポイント: {new_points}")
            print(f"[DEBUG] create_result_embed - ポイントユニットID: {point_unit_id}")
            
            # ポイント単位の取得
            point_unit_name = settings.global_settings.point_unit
            if settings.global_settings.multiple_points_enabled:
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    None
                )
                if point_unit:
                    point_unit_name = point_unit.name
            
            embed = discord.Embed(title=f"{gacha_settings.name}の結果", color=0x00ff00)
            embed.add_field(name="獲得アイテム", value=result_item['name'], inline=False)
            embed.add_field(
                name="ポイント", 
                value=f"+{points}{point_unit_name}",
                inline=False
            )
            embed.add_field(
                name="合計ポイント",
                value=f"{new_points}{point_unit_name}",
                inline=False
            )

            # メッセージ設定の確認と表示
            message_settings = result_item.get('message_settings', {})
            if message_settings.get('enabled', False) and message_settings.get('message'):
                # メッセージ内の変数を置換
                win_message = message_settings['message'].format(
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

    async def _handle_error(self, interaction: discord.Interaction, message: str):
        """エラーハンドリング"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(message, ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
        except Exception:
            print("Failed to send error message to user")
        
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

            # 特定のガチャ設定を取得
            gacha_settings = next(
                (gacha for gacha in settings.gacha_settings.gacha_list 
                if gacha.gacha_id == self.gacha_id),
                None
            )
            
            if not gacha_settings:
                await interaction.response.send_message(
                    "このガチャの設定が見つかりません。",
                    ephemeral=True
                )
                return
            
            # ポイントユニットIDを取得（複数ポイント管理が有効な場合）
            point_unit_id = (
                gacha_settings.point_unit_id 
                if settings.global_settings.multiple_points_enabled 
                else "1"
            )
            
            # 日付チェック
            jst = pytz.timezone('Asia/Tokyo')
            today = datetime.now(jst).strftime('%Y-%m-%d')
            
            # キャッシュからデータを取得（gacha_idを含める）
            cache_key = f"{user_id}_{server_id}_{self.gacha_id}_gacha_result"
            cached_data = self.bot.cache.get(cache_key)

            # 既にガチャを引いている場合の処理
            if cached_data and cached_data.get('last_gacha_date') == today:
                last_item = cached_data.get('last_item', '不明')
                last_points = cached_data.get('last_points', 0)
                total_points = await self.bot.point_manager.get_points(server_id, user_id, point_unit_id)
                print(f"[DEBUG] 今日のガチャは既に実行済みです - ユーザーID: {user_id}, 最後のアイテム: {last_item}, 獲得ポイント: {last_points}, 合計ポイント: {total_points}")

                # ポイント単位の取得
                unit_name = next(
                    (unit.name for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    settings.global_settings.point_unit
                )

                embed = discord.Embed(title=f"今日の{gacha_settings.name}の結果", color=0x00ff00)
                embed.add_field(name="獲得アイテム", value=last_item, inline=False)
                embed.add_field(
                    name="獲得ポイント", 
                    value=f"+{last_points}{unit_name}", 
                    inline=False
                )
                embed.add_field(
                    name="合計ポイント", 
                    value=f"{total_points}{unit_name}", 
                    inline=False
                )
                embed.set_footer(text="また明日挑戦してください！")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # アニメーション表示（ガチャ未実行の場合のみ）
            if gacha_settings.media and gacha_settings.media.gacha_animation_gif:
                animation_embed = discord.Embed(title=f"{gacha_settings.name}実行中...", color=0x00ff00)
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

            # キャッシュに結果を保存（その日のガチャ結果として）
            self.bot.cache[cache_key] = {
                'last_gacha_date': today,
                'last_item': result_item['name'],
                'last_points': points_to_add
            }

            # ポイントを更新（通知も行われる）
            await self.bot.point_manager.update_points(
                user_id,
                server_id,
                points_to_add,  # 直接増加量を指定
                point_unit_id,
                PointSource.GACHA
            )

            # 更新後のポイントを取得
            current_total = await self.bot.point_manager.get_points(server_id, user_id, point_unit_id)

            # ロール付与チェック
            if hasattr(gacha_settings, 'roles') and gacha_settings.roles:
                for role_setting in gacha_settings.roles:
                    if (role_setting.condition.type == 'points_threshold' and 
                        current_total >= role_setting.condition.value):
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

            # 結果表示用のEmbedとViewの作成
            result_embed = await self._create_result_embed(
                result_item, points_to_add, current_total, settings, gacha_settings, interaction, point_unit_id
            )
            
            # X投稿用のViewを作成
            tweet_text = f"{gacha_settings.name}の結果！\n{result_item['name']}を獲得！\n+{points_to_add}ポイント獲得！\n"

            # 設定からカスタムメッセージを追加（設定がある場合のみ）
            if (gacha_settings.messages and 
                gacha_settings.messages.tweet_message):
                tweet_text += f"\n{gacha_settings.messages.tweet_message}"

            encoded_text = urllib.parse.quote(tweet_text)
            twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            share_view = discord.ui.View(timeout=None)
            share_view.add_item(discord.ui.Button(
                label="結果をXに投稿", 
                url=twitter_url,
                style=discord.ButtonStyle.url,
                emoji="🐦"
            ))

            if gacha_settings.media and gacha_settings.media.gacha_animation_gif:
                # アニメーション表示後、結果で上書き
                await interaction.edit_original_response(embed=result_embed, view=share_view)
            else:
                # 通常の結果表示
                await interaction.followup.send(embed=result_embed, view=share_view, ephemeral=True)

            # 結果送信後、メッセージを追跡用辞書に保存
            if interaction.guild_id not in self.bot.gacha_messages:
                self.bot.gacha_messages[interaction.guild_id] = {}
            
            message = await interaction.original_response()
            self.bot.gacha_messages[interaction.guild_id][interaction.user.id] = {
                'channel_id': interaction.channel_id,
                'message_id': message.id
            }

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            await self._handle_error(interaction, "ガチャの実行中にエラーが発生しました。")


    
    @discord.ui.button(label="ガチャ結果をXに投稿", style=discord.ButtonStyle.secondary, emoji="🐦")
    async def share_to_twitter(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild.id)
            
            # 現在のガチャ結果をキャッシュから取得
            cache_key = f"{user_id}_{server_id}_{self.gacha_id}_gacha_result"
            cached_data = self.bot.cache.get(cache_key)
            
            if not cached_data:
                await interaction.response.send_message(
                    "ガチャ結果が見つかりません。先にガチャを回してください。",
                    ephemeral=True
                )
                return
            
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)

            # ガチャ設定を取得
            gacha_settings = next(
                (gacha for gacha in settings.gacha_settings.gacha_list 
                if gacha.gacha_id == self.gacha_id),
                None
            )
            
            if not gacha_settings:
                await interaction.response.send_message(
                    "ガチャ設定が見つかりません。",
                    ephemeral=True
                )
                return

            # ポイント単位の取得
            point_unit_id = (
                gacha_settings.point_unit_id 
                if settings.global_settings.multiple_points_enabled 
                else "1"
            )
            point_unit_name = settings.global_settings.point_unit
            if settings.global_settings.multiple_points_enabled:
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    None
                )
                if point_unit:
                    point_unit_name = point_unit.name

            # X投稿用のテキストを作成
            tweet_text = f"{gacha_settings.name}の結果！\n{cached_data['last_item']}を獲得！\n+{cached_data['last_points']}{point_unit_name}獲得！\n"
            
            # 設定から追加メッセージを追加（設定がある場合のみ）
            if (gacha_settings.messages and 
                gacha_settings.messages.tweet_message):
                tweet_text += f"\n{gacha_settings.messages.tweet_message}"

            # URLエンコードしてX投稿用のURLを生成
            import urllib.parse
            encoded_text = urllib.parse.quote(tweet_text)
            twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            # ボタン付きのメッセージを送信
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Xで投稿", 
                url=twitter_url,
                style=discord.ButtonStyle.url
            ))
            
            await interaction.response.send_message(
                "下のボタンをクリックしてXに投稿できます！",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            await self._handle_error(interaction, "X投稿リンクの生成中にエラーが発生しました。")

    # GachaViewクラスに以下のメソッドを追加
    @discord.ui.button(label="ポイントを確認", style=discord.ButtonStyle.success)
    async def check_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild.id)
            
            settings = await self.bot.get_server_settings(server_id)
            if not settings:
                await interaction.response.send_message(
                    "設定の取得に失敗しました。",
                    ephemeral=True
                )
                return

            # 新しいデザインのEmbed
            embed = discord.Embed(color=0x2f3136)
            embed.set_author(
                name=f"{interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            # 特定のガチャ設定を取得
            gacha_settings = next(
                (gacha for gacha in settings.gacha_settings.gacha_list 
                if gacha.gacha_id == self.gacha_id),
                None
            )
            
            if not gacha_settings:
                await interaction.response.send_message(
                    "ガチャ設定が見つかりません。",
                    ephemeral=True
                )
                return

            if settings.global_settings.multiple_points_enabled:
                # 複数ポイント管理が有効な場合
                point_unit_id = gacha_settings.point_unit_id
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    None
                )
                point_unit_name = point_unit.name if point_unit else settings.global_settings.point_unit
                total_points = await self.bot.point_manager.get_points(server_id, user_id, point_unit_id)

                # このポイント種別でのランキングを取得
                server_rankings = await self.bot.db.get_server_user_rankings(server_id)
                filtered_rankings = [
                    rank for rank in server_rankings 
                    if rank.get('unit_id', '1') == point_unit_id
                ]
            else:
                # 単一ポイント管理の場合
                point_unit_name = settings.global_settings.point_unit
                total_points = await self.bot.point_manager.get_points(server_id, user_id)
                server_rankings = await self.bot.db.get_server_user_rankings(server_id)
                filtered_rankings = server_rankings

            total_members = interaction.guild.member_count
            user_server_rank = next(
                (i + 1 for i, rank in enumerate(filtered_rankings) 
                if str(rank['user_id']) == str(user_id)),
                len(filtered_rankings) + 1
            )

            # RANKとPOINTを大きく表示
            rank_display = f"```fix\n{user_server_rank}/{total_members}```"
            points_display = f"```yaml\n{total_points:,} {point_unit_name}```"

            # 基本情報を表示
            embed.add_field(
                name="RANK",
                value=rank_display,
                inline=True
            )
            embed.add_field(
                name=f"POINT ({gacha_settings.name})",
                value=points_display,
                inline=True
            )

            # 複数ポイント管理が有効な場合、他のポイント情報も表示
            if settings.global_settings.multiple_points_enabled:
                embed.add_field(name="\u200b", value="\u200b", inline=False)  # 空白行を追加
                embed.add_field(
                    name="その他のポイント",
                    value="以下は他のポイント種別の残高です：",
                    inline=False
                )
                
                for unit in settings.global_settings.point_units:
                    if unit.unit_id != point_unit_id:  # 現在のポイント以外を表示
                        other_points = await self.bot.point_manager.get_points(server_id, user_id, unit.unit_id)
                        embed.add_field(
                            name=unit.name,
                            value=f"{other_points:,} pt",
                            inline=True
                        )

            await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            await self._handle_error(interaction, "ポイントの確認中にエラーが発生しました。")

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.midnight_cleanup.start()

    def cog_unload(self):
        self.midnight_cleanup.cancel()

    @tasks.loop(time=datetime_time(hour=0, minute=0, tzinfo=pytz.timezone('Asia/Tokyo')))
    async def midnight_cleanup(self):
        """午前0時にガチャ結果メッセージを削除"""
        for guild_id, user_messages in self.bot.gacha_messages.items():
            for user_id, data in user_messages.items():
                try:
                    channel = self.bot.get_channel(data['channel_id'])
                    if channel:
                        message = await channel.fetch_message(data['message_id'])
                        await message.delete()
                except Exception as e:
                    print(f"メッセージの削除中にエラーが発生: {e}")

        # 追跡用辞書をクリア
        self.bot.gacha_messages.clear()

    @midnight_cleanup.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    def _check_permissions(self, channel, required_perms):
        """チャンネルでの権限を確認し、不足している権限をリストで返す"""
        permissions = channel.permissions_for(channel.guild.me)
        missing_perms = []

        for perm, value in required_perms.items():
            if getattr(permissions, perm, None) != value:
                missing_perms.append(perm)
                print(f"[ERROR] Missing permission: {perm}")

        return missing_perms
    
    
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
            
        return embed
    
    
    async def _create_panel_embed(self, settings: GachaSettings, server_settings = None) -> discord.Embed:
        """パネル用Embedの作成"""
        # デイリーメッセージを取得
        daily_message = (
            settings.messages.daily
            if settings.messages and settings.messages.daily
            else "1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。"
        )

        # Embed の作成
        embed = discord.Embed(
            title="デイリーガチャ",
            description=daily_message,
            color=0x00ff00
        )
        
        # メディアのバナー設定
        if settings.media and settings.media.banner_gif:
            embed.set_image(url=settings.media.banner_gif)

        # 複数ポイント管理が有効な場合、ポイント単位情報を追加
        if server_settings and server_settings.global_settings.multiple_points_enabled:
            point_unit = next(
                (unit for unit in server_settings.global_settings.point_units 
                if unit.unit_id == settings.point_unit_id),
                None
            )
            if point_unit:
                embed.add_field(
                    name="ポイント単位",
                    value=point_unit.name,
                    inline=False
                )
            
        return embed

    @app_commands.command(name="gacha_setup", description="ガチャの初期設定とパネルを設置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def gacha_setup(self, interaction: discord.Interaction):
        """ガチャの初期設定とパネルの設置"""
        try:

            # サーバーIDとチャンネルIDを先に取得
            server_id = str(interaction.guild_id)
            channel_id = str(interaction.channel_id)

            # チャンネル名を取得
            channel = interaction.channel
            channel_name = channel.name
            gacha_name = f"ガチャ-{channel_name}"

            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)

            # 設定をチェック
            if not settings.gacha_settings.enabled:
                await interaction.followup.send("このサーバーではガチャ機能が無効になっています。", ephemeral=True)
                return

            required_permissions = {
                "send_messages": True,
                "embed_links": True,
                "attach_files": True,
                "use_external_emojis": True,
            }

            # 権限チェック
            missing_perms = self._check_permissions(interaction.channel, required_permissions)
            if missing_perms:
                permission_names = {
                    'send_messages': 'メッセージを送信',
                    'embed_links': '埋め込みリンク',
                    'attach_files': 'ファイルを添付',
                    'use_external_emojis': '外部の絵文字を使用'
                }
                missing_perms_jp = [permission_names.get(perm, perm) for perm in missing_perms]
                await interaction.response.send_message(
                    f"チャンネル設定で以下の権限をボットに付与してください：\n"
                    f"```\n{', '.join(missing_perms_jp)}\n```",
                    ephemeral=True
                )
                return

            # # インタラクションを遅延
            # await interaction.response.defer(ephemeral=True)

            # gacha_listの存在確認と初期化
            gacha_feature = settings.gacha_settings
            if not isinstance(gacha_feature, GachaFeatureSettings):
                gacha_feature = GachaFeatureSettings(enabled=True)

            # gacha_listがNoneまたはリストでない場合の処理を追加
            if not hasattr(gacha_feature, 'gacha_list') or not isinstance(gacha_feature.gacha_list, list):
                gacha_feature.gacha_list = []

            # チャンネルの重複チェック
            for existing_gacha in gacha_feature.gacha_list:  # gacha_list を直接参照
                if existing_gacha.channel_id == channel_id:  # オブジェクトのプロパティとしてアクセス
                    await interaction.followup.send(
                        "このチャンネルには既にガチャが設定されています。",
                        ephemeral=True
                    )
                    return

            # デフォルト設定からガチャを作成
            default_settings = self.bot.settings_manager._create_default_settings(server_id)
            default_gacha = default_settings.gacha_settings.gacha_list[0]

            # ポイントユニットIDの設定
            point_unit_id = "1"  # デフォルト値
            if settings.global_settings.multiple_points_enabled:
                # 利用可能なポイントユニットがある場合は最初のものを使用
                if settings.global_settings.point_units:
                    point_unit_id = settings.global_settings.point_units[0].unit_id
                    print(f"[DEBUG] Selected point unit ID: {point_unit_id}")

            # 新しいガチャ設定を GachaSettings 型で作成
            new_gacha = GachaSettings(
                gacha_id=channel_id,  # チャンネルIDをガチャIDとして使用
                name=gacha_name,      # "ガチャ-チャンネル名" の形式
                channel_id=channel_id,
                enabled=True,
                messages=default_gacha.messages,  # デフォルト設定を継承
                media=default_gacha.media,        # デフォルト設定を継承
                items=default_gacha.items,
                point_unit_id=point_unit_id  # ポイントユニットIDを設定
            )

            # gacha_listに追加
            gacha_feature.gacha_list.append(new_gacha)
            settings.gacha_settings = gacha_feature

            # print(f"[DEBUG] Updated gacha_feature type: {type(gacha_feature)}")
            # print(f"[DEBUG] Updated gacha_feature content: {gacha_feature}")

            # 設定を保存
            if not await self.bot.settings_manager.update_settings(server_id, settings):
                await interaction.followup.send(
                    "ガチャ設定の保存に失敗しました。",
                    ephemeral=True
                )
                return

            # パネルの作成と送信
            embed = await self._create_panel_embed(new_gacha)
            view = GachaView(self.bot, new_gacha.gacha_id)  # 修正
            await interaction.channel.send(embed=embed, view=view)

            # 完了メッセージ
            point_unit_name = settings.global_settings.point_unit
            if settings.global_settings.multiple_points_enabled:
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    None
                )
                if point_unit:
                    point_unit_name = point_unit.name
                    
            setup_complete_embed = discord.Embed(
                title="セットアップ完了",
                description=f"ガチャパネルの設置が完了しました。\nポイント単位: {point_unit_name}",
                color=0x00ff00
            )
            temp_message = await interaction.channel.send(embed=setup_complete_embed)

            await asyncio.sleep(3)
            try:
                await temp_message.delete()
            except Exception as e:
                print(f"[WARN] Failed to delete temporary message: {e}")

            await interaction.followup.send(
                f"ガチャパネルの設置が完了しました！\nポイント単位: {point_unit_name}",
                ephemeral=True
            )

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Setup failed: {error_msg}")
            await interaction.followup.send("ガチャパネルの設置中にエラーが発生しました。", ephemeral=True)

    @app_commands.command(name="setup_additional_gacha", description="追加のガチャを設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_additional_gacha(
        self,
        interaction: discord.Interaction,
        description: Optional[str] = None
    ):
        """追加ガチャの設定とパネルの設置"""
        try:
            server_id = str(interaction.guild_id)
            channel_id = str(interaction.channel_id)
            
            # チャンネル名を取得
            channel = interaction.channel
            channel_name = channel.name
            gacha_name = f"ガチャ-{channel_name}"

            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings or not settings.gacha_settings.enabled:
                await interaction.response.send_message(
                    "このサーバーではガチャ機能が無効になっています。",
                    ephemeral=True
                )
                return

            # チャンネルの重複チェック
            for existing_gacha in settings.gacha_settings.gacha_list:
                if existing_gacha.channel_id == channel_id:
                    await interaction.response.send_message(
                        "このチャンネルには既にガチャが設定されています。",
                        ephemeral=True
                    )
                    return

            # ポイントユニットIDの設定
            point_unit_id = "1"  # デフォルト値
            if settings.global_settings.multiple_points_enabled:
                # 利用可能なポイントユニットがある場合は最初のものを使用
                if settings.global_settings.point_units:
                    point_unit_id = settings.global_settings.point_units[0].unit_id
                    print(f"[DEBUG] Selected point unit ID: {point_unit_id}")

            # ポイント単位名の取得
            point_unit_name = settings.global_settings.point_unit
            if settings.global_settings.multiple_points_enabled:
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == point_unit_id),
                    None
                )
                if point_unit:
                    point_unit_name = point_unit.name

            # デフォルト設定からガチャを作成
            default_settings = self.bot.settings_manager._create_default_settings(server_id)
            default_gacha = default_settings.gacha_settings.gacha_list[0]

            # 新しいガチャ設定を作成
            new_gacha = GachaSettings(
                gacha_id=channel_id,
                name=gacha_name,
                channel_id=channel_id,
                description=description,
                enabled=True,
                messages=default_gacha.messages,
                media=default_gacha.media,
                items=default_gacha.items,
                point_unit_id=point_unit_id  # ポイントユニットIDを設定
            )

            # gacha_listに追加
            settings.gacha_settings.gacha_list.append(new_gacha)

            # 設定を保存
            if not await self.bot.settings_manager.update_settings(server_id, settings):
                await interaction.response.send_message(
                    "ガチャ設定の保存に失敗しました。",
                    ephemeral=True
                )
                return

            # パネルの作成と送信
            embed = await self._create_panel_embed(new_gacha, settings)
            view = GachaView(self.bot, new_gacha.gacha_id)
            await interaction.channel.send(embed=embed, view=view)

            # 完了メッセージ
            complete_embed = discord.Embed(
                title="セットアップ完了",
                description=(
                    f"ガチャ「{gacha_name}」の設置が完了しました。\n"
                    f"ポイント単位: {point_unit_name}"
                ),
                color=0x00ff00
            )
            temp_message = await interaction.channel.send(embed=complete_embed)

            await asyncio.sleep(3)
            try:
                await temp_message.delete()
            except Exception as e:
                print(f"[WARN] Failed to delete temporary message: {e}")

            await interaction.response.send_message(
                f"ガチャパネルの設置が完了しました！\nポイント単位: {point_unit_name}",
                ephemeral=True
            )

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Setup failed: {error_msg}")
            await interaction.followup.send("ガチャパネルの設置中にエラーが発生しました。", ephemeral=True)

    @app_commands.command(name="gacha_panel", description="ガチャパネルを設置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def gacha_panel(self, interaction: discord.Interaction):
        """ガチャパネルを設置"""
        try:
            # サーバーIDとチャンネルIDを先に取得
            server_id = str(interaction.guild_id)
            channel_id = str(interaction.channel_id)

            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)

            # デバッグログ
            # print(f"[DEBUG] Retrieved settings for panel setup: {settings}")
            # print(f"[DEBUG] Multiple points enabled: {settings.global_settings.multiple_points_enabled}")

            # 設定をチェック
            if not settings.gacha_settings.enabled:
                await interaction.response.send_message(
                    "このサーバーではガチャ機能が無効になっています。",
                    ephemeral=True
                )
                return

            # 該当チャンネルのガチャを検索
            gacha_settings = next(
                (gacha for gacha in settings.gacha_settings.gacha_list 
                if gacha.channel_id == channel_id),
                None
            )

            if not gacha_settings:
                await interaction.response.send_message(
                    "このチャンネルにはガチャが設定されていません。先に /gacha_setup を実行してください。",
                    ephemeral=True
                )
                return

            # ポイント単位情報を取得
            point_unit_name = settings.global_settings.point_unit
            if settings.global_settings.multiple_points_enabled:
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units 
                    if unit.unit_id == gacha_settings.point_unit_id),
                    None
                )
                if point_unit:
                    point_unit_name = point_unit.name
                    print(f"[DEBUG] Using point unit: {point_unit_name} (ID: {gacha_settings.point_unit_id})")

            # 必要な権限をチェック
            required_permissions = {
                "send_messages": True,
                "embed_links": True,
                "attach_files": True,
                "use_external_emojis": True,
            }

            missing_perms = self._check_permissions(interaction.channel, required_permissions)
            if missing_perms:
                permission_names = {
                    'send_messages': 'メッセージを送信',
                    'embed_links': '埋め込みリンク',
                    'attach_files': 'ファイルを添付',
                    'use_external_emojis': '外部の絵文字を使用'
                }
                missing_perms_jp = [permission_names.get(perm, perm) for perm in missing_perms]
                await interaction.response.send_message(
                    f"チャンネル設定で以下の権限をボットに付与してください：\n"
                    f"```\n{', '.join(missing_perms_jp)}\n```",
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            # パネルの作成と送信
            embed = await self._create_panel_embed(gacha_settings)
            
            # 複数ポイント管理が有効な場合、ポイント単位情報を追加
            if settings.global_settings.multiple_points_enabled:
                embed.add_field(
                    name="ポイント単位",
                    value=point_unit_name,
                    inline=False
                )

            view = GachaView(self.bot, gacha_settings.gacha_id)
            await interaction.channel.send(embed=embed, view=view)

            # 一時的な成功メッセージを送信
            complete_embed = discord.Embed(
                title="ガチャパネル設置完了",
                description=(
                    f"ガチャ「{gacha_settings.name}」のパネルを設置しました。\n"
                    f"ポイント単位: {point_unit_name}"
                ),
                color=0x00ff00
            )
            temp_message = await interaction.channel.send(embed=complete_embed)

            # 一時メッセージを3秒後に削除
            await asyncio.sleep(3)
            try:
                await temp_message.delete()
            except Exception as e:
                print(f"[WARN] Failed to delete temporary message: {e}")

            await interaction.followup.send(
                f"ガチャパネルの設置が完了しました！\nポイント単位: {point_unit_name}",
                ephemeral=True
            )

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Panel setup failed: {error_msg}")
            await interaction.followup.send(
                "ガチャパネルの設置中にエラーが発生しました。",
                ephemeral=True
            )

    @app_commands.command(name="set_tweet_message", description="X投稿時の追加メッセージを設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_tweet_message(
        self,
        interaction: discord.Interaction,
        message: Optional[str] = None,
        gacha_id: Optional[str] = None
    ):
        server_id = str(interaction.guild_id)
        settings = await self.bot.get_server_settings(server_id)
        
        if not settings:
            await interaction.response.send_message(
                "設定の取得に失敗しました。",
                ephemeral=True
            )
            return


        gacha_feature = settings['feature_settings'].get('gacha', {})
        if not isinstance(gacha_feature, dict) or 'gacha_list' not in gacha_feature:
            await interaction.response.send_message(
                "ガチャ設定が見つかりません。",
                ephemeral=True
            )
            return

        if gacha_id:
            # 特定のガチャのメッセージを更新
            gacha = next(
                (g for g in settings.gacha_settings.gacha_list if g.gacha_id == gacha_id),
                None
            )
            if not gacha:
                await interaction.response.send_message(
                    "指定されたガチャが見つかりません。",
                    ephemeral=True
                )
                return

            if 'messages' not in gacha:
                gacha['messages'] = {}
            
            gacha.messages.tweet_message = message
        else:
            # チャンネルに紐づくガチャを検索
            channel_id = str(interaction.channel_id)
            gacha = next(
                (g for g in settings.gacha_settings.gacha_list if g.channel_id == channel_id),
                None
            )
            if not gacha:
                await interaction.response.send_message(
                    "このチャンネルにはガチャが設定されていません。",
                    ephemeral=True
                )
                return
            
            if 'messages' not in gacha:
                gacha['messages'] = {}
            gacha['messages']['tweet_message'] = message

        # 設定を保存
        if await self.bot.update_server_settings(server_id, settings):
            response = f"ガチャ「{gacha['name']}」のX投稿時の追加メッセージを設定しました。" if message else f"ガチャ「{gacha['name']}」のX投稿時の追加メッセージを削除しました。"
            await interaction.response.send_message(response, ephemeral=True)
        else:
            await interaction.response.send_message("設定の保存に失敗しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Gacha(bot))