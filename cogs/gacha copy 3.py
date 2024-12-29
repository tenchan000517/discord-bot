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

            # 結果表示用のEmbedとViewの作成
            result_embed = await self._create_result_embed(
                result_item, points_to_add, new_points, settings, gacha_settings, interaction
            )
            
            # X投稿用のViewを作成
            tweet_text = f"ガチャ結果！\n{result_item['name']}を獲得！\n+{points_to_add}ポイント獲得！\n"

            # 設定からカスタムメッセージを追加（設定がある場合のみ）
            if (settings.gacha_settings.messages and 
                settings.gacha_settings.messages.tweet_message):
                tweet_text += f"\n{settings.gacha_settings.messages.tweet_message}"

            encoded_text = urllib.parse.quote(tweet_text)
            twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
            
            share_view = discord.ui.View(timeout=None)  # タイムアウトなしに設定
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
            name="ポイント", 
            value=f"+{points}{settings.global_settings.point_unit}",
            inline=False
        )
        embed.add_field(
            name="合計ポイント",
            value=f"{new_points}{settings.global_settings.point_unit}",
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
    
    @discord.ui.button(label="ガチャ結果をXに投稿", style=discord.ButtonStyle.secondary, emoji="🐦")
    async def share_to_twitter(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = str(interaction.user.id)
            server_id = str(interaction.guild.id)
            
            # 現在のガチャ結果をキャッシュから取得
            cache_key = f"{user_id}_{server_id}_gacha_result"
            cached_data = self.bot.cache.get(cache_key)
            
            if not cached_data:
                await interaction.response.send_message(
                    "ガチャ結果が見つかりません。先にガチャを回してください。",
                    ephemeral=True
                )
                return
            
            # サーバー設定を取得して追加メッセージをチェック
            settings = await self.bot.get_server_settings(server_id)

            # X投稿用のテキストを作成
            tweet_text = f"ガチャ結果！\n{cached_data['last_item']}を獲得！\n+{cached_data['last_points']}ポイント獲得！\n"
            
            # 設定から追加メッセージを追加（設定がある場合のみ）
            if (settings.gacha_settings.messages and 
                settings.gacha_settings.messages.tweet_message):
                tweet_text += f"\n{settings.gacha_settings.messages.tweet_message}"

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
            
            total_points = await self.bot.point_manager.get_points(server_id, user_id)
            server_rankings = await self.bot.db.get_server_user_rankings(server_id)
            total_members = interaction.guild.member_count
            user_server_rank = next(
                (i + 1 for i, rank in enumerate(server_rankings) 
                if str(rank['user_id']) == str(user_id)),
                len(server_rankings) + 1
            )

            # 新しいデザインのEmbed
            embed = discord.Embed(color=0x2f3136)

            # ユーザー名とアバターを横並びで表示
            embed.set_author(
                name=f"{interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )

            # RANKとPOINTを大きく表示（装飾文字を使用）
            rank_display = f"```fix\n{user_server_rank}/{total_members}```"  # ランクとトータルメンバー数を表示
            points_display = f"```yaml\n{total_points:,} {settings.global_settings.point_unit}```"  # yaml構文で別の色で表示

            embed.add_field(
                name="RANK",
                value=rank_display,
                inline=True
            )
            embed.add_field(
                name="POINT",
                value=points_display,
                inline=True
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

    @app_commands.command(name="gacha_setup", description="ガチャの初期設定とパネルを設置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def gacha_setup(self, interaction: discord.Interaction):
        """ガチャの初期設定とパネルの設置"""

        def check_permissions(channel, required_perms):
            permissions = channel.permissions_for(channel.guild.me)
            missing_perms = []

            # 権限チェックのログ
            print(f"[DEBUG] Permissions Detail: {permissions}")
            print(f"[DEBUG] Channel Info: Name={channel.name}, ID={channel.id}, Type={channel.type}")

            for perm, value in required_perms.items():
                if getattr(permissions, perm, None) != value:
                    missing_perms.append(perm)
                    print(f"[ERROR] Missing permission: {perm}")

            return len(missing_perms) == 0

        # 必要な権限リスト
        required_permissions = {
            "send_messages": True,
            "embed_links": True,
            "attach_files": True,
            "use_external_emojis": True,
        }

        if not check_permissions(interaction.channel, required_permissions):
            await interaction.response.send_message(
                "ボットに必要な権限が不足しています。管理者に確認してください。",
                ephemeral=True
            )
            print("[ERROR] Bot lacks necessary permissions.")
            return

        try:
            server_id = str(interaction.guild_id)
            user_name = interaction.user.display_name
            server_name = interaction.guild.name

            print(f"[INFO] `/gacha_setup` executed by {user_name} in server '{server_name}' (ID: {server_id})")
            print(f"[INFO] Command executed at: {datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()}")

            settings = await self.bot.get_server_settings(server_id)
            print(f"[DEBUG] Retrieved settings: {settings}")

            if not settings.global_settings.features_enabled.get('gacha', True):
                await interaction.response.send_message("このサーバーではガチャ機能が無効になっています。", ephemeral=True)
                print(f"[WARN] Gacha feature is disabled in server '{server_name}' (ID: {server_id})")
                return

            gacha_settings = settings.gacha_settings
            print(f"[DEBUG] Retrieved gacha_settings: {gacha_settings}")

            embed = await self._create_panel_embed(gacha_settings)
            view = GachaView(self.bot)

            print(f"[DEBUG] Sending panel to channel: {interaction.channel.name} (ID: {interaction.channel.id})")

            await interaction.response.send_message("ガチャパネルを設置します...", ephemeral=True)
            panel_message = await interaction.channel.send(embed=embed, view=view)

            temp_message = await interaction.channel.send(
                embed=discord.Embed(
                    title="セットアップ完了",
                    description="ガチャパネルの設置が完了しました。",
                    color=0x00ff00
                )
            )

            print(f"[INFO] Gacha panel successfully set up in server '{server_name}' (ID: {server_id})")
            print(f"[DEBUG] Panel message ID: {panel_message.id}")

            await asyncio.sleep(3)
            try:
                await temp_message.delete()
            except Exception as e:
                print(f"[WARN] Failed to delete temporary message: {e}")

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Setup failed: {error_msg}")
            await interaction.response.send_message("ガチャパネルの設置中にエラーが発生しました。", ephemeral=True)


    @app_commands.command(name="gacha_panel", description="ガチャパネルを設置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def gacha_panel(self, interaction: discord.Interaction):  # ctx -> interaction
        """ガチャパネルを設置"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            print(f"[DEBUG] settings: {settings}")

            if not settings.global_settings.features_enabled.get('gacha', True):
                await interaction.response.send_message("このサーバーではガチャ機能が無効になっています。", ephemeral=True)
                return

            # 既存のパネルを削除
            try:
                async for message in interaction.channel.history(limit=50):
                    if message.author == self.bot.user and message.embeds and len(message.embeds) > 0:
                        if message.embeds[0].title == "デイリーガチャ":
                            await message.delete()
            except Exception as e:
                print(f"Failed to delete old panel: {e}")

            gacha_settings = settings.gacha_settings
            print(f"[DEBUG] gacha_settings: {gacha_settings}")

            embed = await self._create_panel_embed(gacha_settings)
            view = GachaView(self.bot)
            await interaction.response.send_message(embed=embed, view=view)
            
            success_embed = discord.Embed(
                title="セットアップ完了",
                description="ガチャパネルの設置が完了しました。",
                color=0x00ff00
            )
            temp_message = await interaction.channel.send(embed=success_embed)
            
            await asyncio.sleep(3)
            try:
                await temp_message.delete()
            except Exception as e:
                print(f"[WARN] Failed to delete temporary message: {e}")

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] gacha_panel failed: {error_msg}")
            await interaction.response.send_message("ガチャパネルの設置中にエラーが発生しました。", ephemeral=True)

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
    
    @app_commands.command(name="set_tweet_message", description="X投稿時の追加メッセージを設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_tweet_message(self, interaction: discord.Interaction, message: Optional[str] = None):
        server_id = str(interaction.guild_id)
        settings = await self.bot.get_server_settings(server_id)
        
        if not settings:
            await interaction.response.send_message("設定の取得に失敗しました。", ephemeral=True)
            return

        # メッセージを更新
        new_settings = {
            'enabled': settings.gacha_settings.enabled,
            'messages': {
                'setup': settings.gacha_settings.messages.setup,
                'daily': settings.gacha_settings.messages.daily,
                'win': settings.gacha_settings.messages.win,
                'custom_messages': settings.gacha_settings.messages.custom_messages,
                'tweet_message': message  # 新しいメッセージを設定（Noneの場合は追加メッセージなし）
            },
            'media': settings.gacha_settings.media.to_dict() if settings.gacha_settings.media else None,
            'items': settings.gacha_settings.items
        }
        
        success = await self.bot.db.update_feature_settings(server_id, 'gacha', new_settings)
        
        if success:
            response = "X投稿時の追加メッセージを設定しました。" if message else "X投稿時の追加メッセージを削除しました。"
            await interaction.response.send_message(response, ephemeral=True)
        else:
            await interaction.response.send_message("設定の更新に失敗しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Gacha(bot))