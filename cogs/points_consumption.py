import discord
from discord import app_commands
from discord.ext import commands
import traceback
from datetime import datetime
import pytz
from models.server_settings import PointConsumptionFeatureSettings, PointConsumptionModalSettings, ServerSettings, PointUnit
import asyncio
import re
from typing import Optional
from decimal import Decimal

class PointsConsumption(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._consumption_locks = {}  # 重複実行防止用

    @app_commands.command(name="setup_consumption", description="ポイント消費機能の初期設定を行います")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_consumption(self, interaction: discord.Interaction):
        """ポイント消費機能の初期設定とパネル設置"""
        try:
            server_id = str(interaction.guild_id)
            channel_id = str(interaction.channel_id)
            
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings:
                await interaction.response.send_message(
                    "サーバー設定の取得に失敗しました。",
                    ephemeral=True
                )
                return
                
            # 既存の消費設定をチェック
            consumption_settings = settings.point_consumption_settings
            if consumption_settings and consumption_settings.enabled:
                await interaction.response.send_message(
                    "このサーバーには既にポイント消費機能が設定されています。\n"
                    "パネルを再設置する場合は `/consumption_panel` を使用してください。",
                    ephemeral=True
                )
                return

            # 初期設定を作成
            default_settings = self.bot.settings_manager._create_default_settings(server_id)
            consumption_settings = default_settings.point_consumption_settings
            consumption_settings.enabled = True
            settings.point_consumption_settings = consumption_settings

            # 設定を保存
            if not await self.bot.settings_manager.update_settings(server_id, settings):
                await interaction.response.send_message(
                    "設定の保存に失敗しました。",
                    ephemeral=True
                )
                return

            # パネルを設置
            await self._setup_consumption_panel(interaction, settings)

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Setup failed: {error_msg}")
            await interaction.followup.send(
                "設定中にエラーが発生しました。",
                ephemeral=True
            )

    async def _setup_consumption_panel(self, interaction: discord.Interaction, settings: ServerSettings) -> None:
        """消費パネルのセットアップ - 改善版"""
        try:
            # 応答を遅延させておく
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

            channel = interaction.channel
            if not channel:
                raise ValueError("Channel not found")

            # 消費設定の取得
            consumption_settings = settings.point_consumption_settings
            if not consumption_settings:
                raise ValueError("Point consumption settings not found")

            # 既存のボットメッセージを削除
            print("[DEBUG] Cleaning up existing messages...")
            try:
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user:
                        try:
                            await message.delete()
                            print(f"[DEBUG] Deleted message: {message.id}")
                            await asyncio.sleep(0.5)  # Discord APIの制限を考慮
                        except Exception as e:
                            print(f"[DEBUG] Message deletion error: {e}")
            except Exception as e:
                print(f"[ERROR] Error while cleaning up messages: {e}")

            # パネルのメッセージを設定
            panel_title = consumption_settings.panel_title
            
            # 利用可能なポイントプールの取得
            point_units = settings.global_settings.point_units
            print(f"[DEBUG] Found {len(point_units)} point units")
            
            # Embedの作成
            embed = discord.Embed(
                title=panel_title,
                description=consumption_settings.panel_message,
                color=discord.Color.blue()
            )
            # embed.set_footer(text=f"Setup at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Viewの作成
            view = discord.ui.View(timeout=None)
            for unit in point_units:
                button = discord.ui.Button(
                    label=f"{consumption_settings.button_name} ({unit.name})",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"consume_points_{unit.unit_id}"
                )
                view.add_item(button)

            # パネルを送信
            panel_message = await channel.send(embed=embed, view=view)

            # 完了メッセージを送信
            complete_embed = discord.Embed(
                title="セットアップ完了",
                description="ポイント消費パネルの設置が完了しました。",
                color=discord.Color.green()
            )
            
            # 一時的な完了メッセージを送信
            temp_message = await channel.send(embed=complete_embed)
            await asyncio.sleep(3)
            await temp_message.delete()

            # インタラクションに応答
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "ポイント消費パネルの設置が完了しました！",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "ポイント消費パネルの設置が完了しました！",
                    ephemeral=True
                )

        except Exception as e:
            print(f"[ERROR] Error in setup_consumption_panel: {e}")
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "パネルの設置中にエラーが発生しました。",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "パネルの設置中にエラーが発生しました。",
                    ephemeral=True
                )
                
    @app_commands.command(name="consumption_panel", description="ポイント消費パネルを設置します")
    @app_commands.checks.has_permissions(administrator=True)
    async def consumption_panel(self, interaction: discord.Interaction):
        """ポイント消費パネルの設置"""
        try:
            server_id = str(interaction.guild_id)
            
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings or not settings.point_consumption_settings or not settings.point_consumption_settings.enabled:
                await interaction.response.send_message(
                    "ポイント消費機能が設定されていません。先に `/setup_consumption` を実行してください。",
                    ephemeral=True
                )
                return

            # パネルを設置
            await self._setup_consumption_panel(interaction, settings)

        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERROR] Panel setup failed: {error_msg}")
            await interaction.followup.send(
                "パネル設置中にエラーが発生しました。",
                ephemeral=True
            )

    async def create_consumption_request(
        self,
        guild_id: str,
        user_id: str,
        points: int,
        unit_id: str,  # 追加
        thread_id: str = None,
        wallet_address: str = None,
        email: str = None
    ) -> dict:
        """
        
        消費リクエストの作成
        
        呼び出し先
        aws_database.py
            save_consumption_history
        
        """
        try:
            timestamp = datetime.now(pytz.UTC).isoformat()
            request_data = {
                'server_id': str(guild_id),
                'user_id': str(user_id),
                'points': points,
                'timestamp': timestamp,
                'thread_id': thread_id,
                'status': 'pending',
                'wallet_address': wallet_address,
                'email': email,
                'created_at': timestamp,
                'unit_id': unit_id  # 追加
            }
            
            # データベースに保存
            success = await self.bot.db.save_consumption_history(request_data)
            if not success:
                raise Exception("Failed to save consumption request")

            return request_data

        except Exception as e:
            print(f"Error creating consumption request: {e}")
            return None

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """インタラクションハンドラー - デバッグログ強化版"""
        try:
            if not interaction.data or 'custom_id' not in interaction.data:
                return

            print(f"[DEBUG] Received interaction with custom_id: {interaction.data['custom_id']}")

            # サーバー設定の取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            # settings の中身を確認
            print(f"[DEBUG] Retrieved modal_settings.fields: {settings.point_consumption_settings.modal_settings.fields}")
            print(f"[DEBUG] wallet field directly after retrieval: {settings.point_consumption_settings.modal_settings.fields.get('wallet')}")

            # 設定情報の詳細ログ
            print(f"[DEBUG] Server settings loaded: {settings is not None}")
            if settings:
                print("[DEBUG] Global settings:")
                print(f"  - Point units: {[unit.__dict__ for unit in settings.global_settings.point_units]}")
                print(f"  - Features enabled: {settings.global_settings.features_enabled}")
                print(f"  - Multiple points enabled: {settings.global_settings.multiple_points_enabled}")
                
                print("[DEBUG] Point consumption settings:")
                if settings.point_consumption_settings:
                    print(f"  - Enabled: {settings.point_consumption_settings.enabled}")
                    print(f"  - Button name: {settings.point_consumption_settings.button_name}")
                    print(f"  - Panel message: {settings.point_consumption_settings.panel_message}")
                    print(f"  - Thread welcome message: {settings.point_consumption_settings.thread_welcome_message}")
                else:
                    print("  - No point consumption settings found")

            if not settings or not settings.point_consumption_settings:
                await interaction.response.send_message(
                    "ポイント消費機能の設定が見つかりません。",
                    ephemeral=True
                )
                return

            # ボタンのカスタムID処理
            custom_id = interaction.data['custom_id']
            print(f"[DEBUG] Processing custom_id: {custom_id}")

            if custom_id.startswith('consume_points_'):
                print("[DEBUG] Handling consume points button")
                await self.handle_consume_button(interaction)
                
            elif custom_id.startswith('show_consumption_modal_'):
                print("[DEBUG] Handling show modal button")
                unit_id = custom_id.split('_')[-1]
                print(f"[DEBUG] Unit ID from custom_id: {unit_id}")
                
                available_points = await self.bot.point_manager.get_points(
                    str(interaction.guild_id),
                    str(interaction.user.id),
                    unit_id
                )
                print(f"[DEBUG] Available points: {available_points}")
                
                modal = PointConsumptionModal(
                    settings,
                    available_points,
                    unit_id,
                    interaction  # インタラクションを渡す

                )
                await modal.initialize_wallet()  # ウォレットアドレスの初期化
                await interaction.response.send_modal(modal)
                
            elif custom_id.startswith('approve_consume_'):
                print("[DEBUG] Handling approve button")
                print(f"[DEBUG] Custom ID parts: {custom_id.split('_')}")
                await self.handle_approve_button(interaction)

            elif custom_id.startswith('cancel_consume_'):
                print("[DEBUG] Handling cancel button")
                await self.handle_cancel_button(interaction)

        except Exception as e:
            print(f"[ERROR] Error in on_interaction: {e}")
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "エラーが発生しました。",
                    ephemeral=True
                )

    # async def get_existing_thread(self, guild: discord.Guild, user_id: str) -> Optional[discord.Thread]:
    #     """指定されたユーザーIDに対応する既存スレッドを取得"""
    #     for thread in guild.threads:
    #         if thread.name == f"ポイント消費-{user_id}" and not thread.archived:
    #             return thread
    #     return None

    async def handle_consume_button(self, interaction: discord.Interaction):
        """ポイント消費ボタンのハンドラー - デバッグログ追加版"""
        try:
            print(f"[DEBUG] Starting handle_consume_button for user {interaction.user.id}")
            print(f"[DEBUG] Custom ID: {interaction.data.get('custom_id')}")
            
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            print(f"[DEBUG] Server settings retrieved: {settings is not None}")
            print(f"[DEBUG] Point consumption settings: {settings.point_consumption_settings is not None if settings else False}")

            if not settings or not settings.point_consumption_settings:
                await interaction.response.send_message(
                    "ポイント消費機能の設定が見つかりません。",
                    ephemeral=True
                )
                return

            # カスタムIDからポイントユニットIDを抽出
            unit_id = interaction.data['custom_id'].split('_')[-1]
            print(f"[DEBUG] Extracted unit_id: {unit_id}")
            
            # ポイントユニット情報の取得
            point_units = settings.global_settings.point_units
            print(f"[DEBUG] Available point units: {[unit.__dict__ for unit in point_units]}")
            
            point_unit = next(
                (unit for unit in settings.global_settings.point_units if unit.unit_id == unit_id),
                None
            )
            print(f"[DEBUG] Found point unit: {point_unit.__dict__ if point_unit else None}")

            if not point_unit:
                await interaction.response.send_message(
                    "無効なポイントプールです。",
                    ephemeral=True
                )
                return

            consumption_settings = settings.point_consumption_settings
            # スレッド名の生成
            thread_name = f"{interaction.user.name}-{point_unit.name}-{consumption_settings.panel_title}"
            print(f"[DEBUG] Generated thread name: {thread_name}")

            # 既存スレッドの検索
            existing_threads = [t for t in interaction.guild.threads if not t.archived]
            print(f"[DEBUG] Found {len(existing_threads)} active threads")
            # print(f"[DEBUG] Active thread names: {[t.name for t in existing_threads]}")
            
            existing_thread = None
            for thread in existing_threads:
                print(f"[DEBUG] Checking thread: {thread.name}")
                if thread.name == thread_name:
                    existing_thread = thread
                    print(f"[DEBUG] Found matching thread: {thread.id}")
                    break

            # 利用可能ポイントの取得
            available_points = await self.bot.point_manager.get_points(
                str(interaction.guild_id),
                str(interaction.user.id),
                unit_id
            )
            print(f"[DEBUG] Available points for user: {available_points}")

            # ウェルカムメッセージの準備
            message = consumption_settings.thread_welcome_message.format(
                user=interaction.user.mention,
                points=available_points,
                unit=point_unit.name
            )
            print(f"[DEBUG] Prepared welcome message")

            # 申請ボタンの作成
            view = discord.ui.View()
            modal_button = discord.ui.Button(
                label="申請する",
                style=discord.ButtonStyle.primary,
                custom_id=f"show_consumption_modal_{unit_id}"
            )
            view.add_item(modal_button)
            print(f"[DEBUG] Created modal button with custom_id: {modal_button.custom_id}")

            if existing_thread:
                print(f"[DEBUG] Using existing thread: {existing_thread.id}")
                await interaction.response.send_message(
                    f"既存のポイント消費申請スレッドが見つかりました。\n{existing_thread.jump_url}",
                    ephemeral=True
                )
                await existing_thread.send(message, view=view)
                return

            # プライベートスレッドの作成
            print(f"[DEBUG] Creating new thread in channel: {interaction.channel.id}")
            try:
                thread = await interaction.channel.create_thread(
                    name=thread_name,
                    auto_archive_duration=1440,
                    type=discord.ChannelType.private_thread
                )
                print(f"[DEBUG] Successfully created thread: {thread.id}")
            except Exception as e:
                print(f"[DEBUG] Error creating thread: {e}")
                raise

            # スレッドの初期化を待つ
            await asyncio.sleep(1)

            # スレッドのセットアップ
            try:
                await thread.add_user(interaction.user)
                print(f"[DEBUG] Added user {interaction.user.id} to thread")

                # 承認ロールを持つメンバーを追加
                if consumption_settings.approval_roles:
                    print(f"[DEBUG] Adding members with approval roles: {consumption_settings.approval_roles}")
                    for member in interaction.guild.members:
                        member_role_ids = [str(role.id) for role in member.roles]
                        if any(role_id in consumption_settings.approval_roles for role_id in member_role_ids):
                            try:
                                await thread.add_user(member)
                                print(f"[DEBUG] Added approver {member.id} to thread")
                            except Exception as e:
                                print(f"[DEBUG] Failed to add member {member.id} to thread: {e}")
                                continue
            except Exception as e:
                print(f"[DEBUG] Error in thread setup: {e}")
                raise

            # 通知の送信
            print(f"[DEBUG] Sending thread creation notification")
            await interaction.response.send_message(
                f"ポイント消費申請用のスレッドを作成しました。\n{thread.jump_url}",
                ephemeral=True
            )

            # ウェルカムメッセージの送信
            try:
                print(f"[DEBUG] Sending welcome message to thread")
                await thread.send(message, view=view)
            except discord.errors.HTTPException as e:
                print(f"[DEBUG] HTTP error sending welcome message: {e}")
                await asyncio.sleep(1)
                await thread.send(message, view=view)

        except Exception as e:
            print(f"[ERROR] Error in handle_consume_button: {e}")
            print(traceback.format_exc())
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "エラーが発生しました。",
                    ephemeral=True
                )

    async def check_approval_permission(
                self, 
                interaction: discord.Interaction, 
                settings: PointConsumptionFeatureSettings
            ) -> bool:
            """承認権限チェック"""
            
            # 管理者権限チェック
            if settings.admin_override and interaction.user.guild_permissions.administrator:
                return True
                
            # 承認ロールチェック
            if settings.approval_roles:
                user_roles = [str(role.id) for role in interaction.user.roles]
                return any(role_id in settings.approval_roles for role_id in user_roles)
            
            return False
    
    async def update_missing_unit_ids(self, server_id: str, settings: ServerSettings) -> bool:
        """
        unit_idが存在しない消費履歴データを更新
        単一ポイントプールのサーバーのみ自動補完
        """
        try:
            if settings.global_settings.multiple_points_enabled:
                print(f"[WARNING] Server {server_id} has multiple points enabled. Manual unit_id mapping required.")
                return False

            # まず全てのデータを取得
            all_records = await asyncio.to_thread(
                self.bot.db.point_consumption_history_table.scan,
                FilterExpression='server_id = :sid',
                ExpressionAttributeValues={
                    ':sid': server_id
                }
            )

            if not all_records.get('Items'):
                return True  # データが存在しない場合は成功扱い

            # unit_idが存在しないレコードを抽出
            records_to_update = [
                record for record in all_records['Items']
                if 'unit_id' not in record
            ]

            if not records_to_update:
                return True  # 更新が必要なレコードが存在しない場合は成功扱い

            # デフォルトのunit_idを取得
            default_unit_id = settings.global_settings.point_units[0].unit_id if settings.global_settings.point_units else "1"

            # 各レコードを更新
            for record in records_to_update:
                try:
                    await asyncio.to_thread(
                        self.bot.db.point_consumption_history_table.update_item,
                        Key={
                            'server_id': server_id,
                            'timestamp': record['timestamp']
                        },
                        UpdateExpression="SET unit_id = :uid",
                        ExpressionAttributeValues={
                            ':uid': default_unit_id
                        }
                    )
                    print(f"[DEBUG] Updated record {record['timestamp']} with unit_id: {default_unit_id}")
                except Exception as e:
                    print(f"[ERROR] Failed to update record {record['timestamp']}: {e}")
                    continue

            return True

        except Exception as e:
            print(f"[ERROR] Error updating missing unit_ids: {e}")
            return False

    async def handle_approve_button(self, interaction: discord.Interaction):
        """承認ボタンのハンドラー"""
        # print("[DEBUG] Starting approval process")
        # print(f"Approval button clicked with params: server_id={interaction.guild_id}, user_id={interaction.user.id}")

        try:
            # インタラクションがまだ応答されていない場合のみdefer
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
                
            # サーバー設定の取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            # print(f"[DEBUG] Retrieved server settings: {settings is not None}")
            # print(f"[DEBUG] Point consumption settings: {settings.point_consumption_settings is not None if settings else False}")
            if not settings or not settings.point_consumption_settings:
                print("[DEBUG] Settings not found")
                await interaction.followup.send(
                    "設定が見つかりません。管理者にお問い合わせください。",
                    ephemeral=True
                )
                return

            consumption_settings = settings.point_consumption_settings
            # print(f"[DEBUG] Retrieved consumption settings: {consumption_settings}")

            # 承認権限チェック
            has_permission = await self.check_approval_permission(
                interaction,
                consumption_settings
            )
            # print(f"[DEBUG] Permission check result: {has_permission}")
            
            if not has_permission:
                # print(f"[DEBUG] User {interaction.user.id} lacks permission")
                await interaction.followup.send(
                    "このアクションを実行する権限がありません。",
                    ephemeral=True
                )
                return

            # カスタムIDから情報を抽出
            try:
                user_id, points, unit_id = self._parse_button_custom_id(interaction.data['custom_id'])
                # print(f"[DEBUG] Parsed button data:")
                # print(f"  user_id: {user_id}")
                # print(f"  points: {points}")
                # print(f"  unit_id: {unit_id}")
                
                # ポイントユニット情報の取得
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units if unit.unit_id == unit_id),
                    None
                )
                # print(f"[DEBUG] Found point unit: {point_unit}")
                
                if not point_unit:
                    # print("[DEBUG] Invalid point pool")
                    await interaction.followup.send(
                        "無効なポイントプールです。",
                        ephemeral=True
                    )
                    return
                
            except ValueError as e:
                # print(f"[ERROR] Invalid custom_id: {e}")
                await interaction.followup.send(
                    "無効なボタンデータです。",
                    ephemeral=True
                )
                return

            # 重複実行防止のロック取得 - unit_id対応
            # print(f"[DEBUG] Acquiring lock for user {user_id} and unit {unit_id}")
            async with await self._get_consumption_lock(user_id, unit_id):
                # print("[DEBUG] Lock acquired")

                # unit_idの補完を実行
                await self.update_missing_unit_ids(str(interaction.guild_id), settings)
                
                # ポイント消費実行
                print(f"[DEBUG] Executing point consumption:")
                print(f"  user_id: {user_id}")
                print(f"  server_id: {str(interaction.guild_id)}")
                print(f"  points: {-points}")
                print(f"  unit_id: {unit_id}")
                print(f"  source: {str(interaction.user.id)}")
                
                wallet_address = latest_request.get('wallet_address')  # ウォレットアドレスを取得

                success = await self.bot.point_manager.consume_points(
                    user_id=user_id,
                    server_id=str(interaction.guild_id),
                    points=points,  # 正の値をそのまま渡す
                    unit_id=unit_id,
                    source=str(interaction.user.id),
                    wallet_address=wallet_address  # ウォレットアドレスを追加
                )
                # print(f"[DEBUG] Point consumption result: {success}")

                if success:
                    # print("[DEBUG] Point consumption successful, updating history")
                    # # 履歴のステータス更新
                    # print(f"[DEBUG] Executing database scan with params:")
                    # print(f"  server_id: {str(interaction.guild_id)}")
                    # print(f"  user_id: {user_id}")
                    # print(f"  status: pending")
                    # print(f"  points: {points}")
                    # print(f"  unit_id: {unit_id}")

                    # まず条件なしでスキャンして全データを確認
                    all_items = await asyncio.to_thread(
                        self.bot.db.point_consumption_history_table.scan
                    )
                    # print("\n[DEBUG] === All records in database ===")
                    for item in all_items.get('Items', []):
                        print(f"Record: {item}")
                    
                    response = await asyncio.to_thread(
                        self.bot.db.point_consumption_history_table.scan,
                        FilterExpression='server_id = :sid AND user_id = :uid AND #status = :status AND points = :p AND unit_id = :unit_id',  # :points を :p に変更
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':sid': str(interaction.guild_id),
                            ':uid': user_id,
                            ':status': 'pending',
                            ':p': Decimal(str(points)),
                            ':unit_id': unit_id
                        }
                    )

                    # print(f"\n[DEBUG] === Scan results ===")
                    # print(f"  Found items: {len(response.get('Items', []))}")
                    # 見つかった各レコードの詳細をログに出力
                    for idx, item in enumerate(response.get('Items', [])):
                        print(f"\n[DEBUG] Record {idx + 1}:")
                        print(f"  Server ID: {item.get('server_id')}")
                        print(f"  User ID: {item.get('user_id')}")
                        print(f"  Points: {item.get('points')}")
                        print(f"  Unit ID: {item.get('unit_id')}")
                        print(f"  Status: {item.get('status')}")
                        print(f"  Timestamp: {item.get('timestamp')}")

                    print(f"[DEBUG] Database scan response:")
                    print(f"  Result: {response}")
                    if not response.get('Items'):  # NOT演算子を追加
                        print("[DEBUG] No matching request found in database")
                        await interaction.followup.send(
                            "リクエストが見つかりません。申請が既に処理されているか、期限切れの可能性があります。",
                            ephemeral=True
                        )
                        return

                    # リクエストが見つかった場合の処理
                    latest_request = sorted(
                        response['Items'],
                        key=lambda x: x['timestamp'],
                        reverse=True
                    )[0]
                    
                    # print("[DEBUG] Updating consumption status")
                    await self.bot.db.update_consumption_status(
                        str(interaction.guild_id),
                        latest_request['timestamp'],
                        'approved',
                        str(interaction.user.id)
                    )

                    # メッセージ削除
                    try:
                        print("[DEBUG] Attempting to delete approval message")
                        await interaction.message.delete()
                    except Exception as e:
                        print(f"[ERROR] Failed to delete approval message: {e}")

                    # 完了メッセージ送信
                    if consumption_settings.completion_message_enabled:
                        # print("[DEBUG] Sending completion message")
                        message = consumption_settings.completion_message.format(
                            user=f"<@{user_id}>",
                            points=points,
                            unit=point_unit.name,
                            admin=interaction.user.mention
                        )
                        # print(f"[DEBUG] Completion message: {message}")
                        await interaction.channel.send(message)

                    # 履歴の記録
                    if consumption_settings.history_enabled and consumption_settings.history_channel_id:
                        # print("[DEBUG] Recording consumption history")
                        await self.log_consumption(
                            interaction.guild_id,
                            {
                                'user_id': user_id,
                                'points': points,
                                'admin_id': str(interaction.user.id),
                            },
                            settings
                        )

                    # print("[DEBUG] Sending success message")
                    # 承認処理完了後のメッセージ送信
                    try:
                        await interaction.followup.send("承認処理が完了しました。", ephemeral=True)
                    except discord.NotFound:
                        # Webhookが見つからない場合は、チャンネルに直接メッセージを送信
                        await interaction.channel.send(
                            f"{interaction.user.mention} 承認処理が完了しました。",
                            ephemeral=True
                        )

        except Exception as e:
            print(f"[ERROR] Exception in approve button: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            await interaction.followup.send(
                "エラーが発生しました。管理者にお問い合わせください。",
                ephemeral=True
            )

    async def _get_consumption_lock(self, user_id: str, unit_id: str):
        """重複実行防止用のロック取得 - unit_id対応版"""
        lock_key = f"{user_id}_{unit_id}"
        if lock_key not in self._consumption_locks:
            self._consumption_locks[lock_key] = asyncio.Lock()
        return self._consumption_locks[lock_key]

    async def handle_cancel_button(self, interaction: discord.Interaction):
        """キャンセルボタンのハンドラー"""
        print("[DEBUG] === Cancel button handler started ===")
        try:
            await interaction.response.defer(ephemeral=True)

            print("[DEBUG] === Server Settings Retrieval ===")
            # サーバー設定の取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            print(f"[DEBUG] Settings retrieved: {settings is not None}")
            print(f"[DEBUG] Settings type: {type(settings)}")
            print(f"[DEBUG] Point consumption settings exists: {settings.point_consumption_settings is not None if settings else False}")

            if not settings or not settings.point_consumption_settings:
                print("[DEBUG] Settings validation failed")
                await interaction.followup.send(
                    "設定が見つかりません。",
                    ephemeral=True
                )
                return

            print("[DEBUG] === Permission Check ===")
            consumption_settings = settings.point_consumption_settings
            print(f"[DEBUG] Consumption settings type: {type(consumption_settings)}")

            # 承認権限チェック
            has_permission = await self.check_approval_permission(
                interaction,
                consumption_settings
            )
            print(f"[DEBUG] Permission check result: {has_permission}")
            
            if not has_permission:
                print("[DEBUG] Permission check failed")
                await interaction.followup.send(
                    "このアクションを実行する権限がありません。",
                    ephemeral=True
                )
                return

            print("[DEBUG] === Custom ID Parsing ===")
            # カスタムIDから情報を抽出
            try:
                custom_id = interaction.data['custom_id']
                print(f"[DEBUG] Raw custom_id: {custom_id}")
                user_id, points, unit_id = self._parse_button_custom_id(custom_id)
                print(f"[DEBUG] Parsed data:")
                print(f"  user_id: {user_id}")
                print(f"  points: {points}")
                print(f"  unit_id: {unit_id}")
                
                print("[DEBUG] === Point Unit Validation ===")
                point_unit = next(
                    (unit for unit in settings.global_settings.point_units if unit.unit_id == unit_id),
                    None
                )
                print(f"[DEBUG] Found point unit: {point_unit}")
                print(f"[DEBUG] Point unit type: {type(point_unit)}")
                
                if not point_unit:
                    print("[DEBUG] Point unit validation failed")
                    await interaction.followup.send(
                        "無効なポイントプールです。",
                        ephemeral=True
                    )
                    return
                    
            except ValueError as e:
                print(f"[ERROR] Custom ID parsing failed: {e}")
                await interaction.followup.send(
                    "無効なボタンデータです。",
                    ephemeral=True
                )
                return
            except Exception as e:
                print(f"[ERROR] Unexpected error in custom ID processing: {e}")
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                await interaction.followup.send(
                    "データの処理中にエラーが発生しました。",
                    ephemeral=True
                )
                return

            print("[DEBUG] === Database Operations ===")
            # 対象の申請を検索
            print("[DEBUG] Starting database scan...")
            try:
                scan_params = {
                    'FilterExpression': 'server_id = :sid AND user_id = :uid AND #status = :status AND points = :p AND unit_id = :unit_id',
                    'ExpressionAttributeNames': {'#status': 'status'},
                    'ExpressionAttributeValues': {
                        ':sid': str(interaction.guild_id),
                        ':uid': user_id,
                        ':status': 'pending',
                        ':p': Decimal(str(points)),
                        ':unit_id': unit_id
                    }
                }
                print(f"[DEBUG] Scan parameters: {scan_params}")

                response = await asyncio.to_thread(
                    self.bot.db.point_consumption_history_table.scan,
                    **scan_params
                )

                print(f"[DEBUG] Database response type: {type(response)}")
                print(f"[DEBUG] Database response keys: {response.keys() if response else 'None'}")
                print(f"[DEBUG] Found items: {len(response.get('Items', []))}")

                if not response.get('Items'):
                    print("[DEBUG] No matching requests found")
                    await interaction.followup.send(
                        "対象の申請が見つかりません。",
                        ephemeral=True
                    )
                    return

                # 最新の申請を取得
                latest_request = sorted(
                    response['Items'],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )[0]
                print(f"[DEBUG] Latest request: {latest_request}")

                print("[DEBUG] === Delete Operations ===")
                # 申請を削除
                delete_params = {
                    'Key': {
                        'server_id': str(interaction.guild_id),
                        'timestamp': latest_request['timestamp']
                    }
                }
                print(f"[DEBUG] Delete parameters: {delete_params}")

                await asyncio.to_thread(
                    self.bot.db.point_consumption_history_table.delete_item,
                    **delete_params
                )
                print("[DEBUG] Database delete operation completed")

                # メッセージ削除
                try:
                    print("[DEBUG] Attempting to delete interaction message")
                    await interaction.message.delete()
                    print("[DEBUG] Message deletion successful")
                except Exception as e:
                    print(f"[ERROR] Message deletion failed: {e}")
                    print(f"[ERROR] Message deletion traceback: {traceback.format_exc()}")

                print("[DEBUG] === Completion Message ===")
                # 完了メッセージ送信
                if consumption_settings.completion_message_enabled:
                    message = f"<@{user_id}>の{points}{point_unit.name}消費申請がキャンセルされました。"
                    print(f"[DEBUG] Sending completion message: {message}")
                    await interaction.channel.send(message)

                print("[DEBUG] === Final Response ===")
                await interaction.followup.send(
                    "キャンセルが完了しました。",
                    ephemeral=True
                )
                print("[DEBUG] === Cancel button handler completed ===")

            except Exception as db_error:
                print(f"[ERROR] Database operation failed: {db_error}")
                print(f"[ERROR] Database error traceback: {traceback.format_exc()}")
                await interaction.followup.send(
                    "データベース操作中にエラーが発生しました。",
                    ephemeral=True
                )

        except Exception as e:
            print(f"[ERROR] Top level error in cancel button handler: {e}")
            print(f"[ERROR] Full error traceback: {traceback.format_exc()}")
            await interaction.followup.send(
                "予期しないエラーが発生しました。",
                ephemeral=True
            )

    async def log_consumption(self, guild_id: str, history_data: dict, settings: ServerSettings):
        """承認済みの消費履歴をログに記録"""
        try:
            consumption_settings = settings.point_consumption_settings

            # history_channel_id が設定されていない、または history_enabled が False の場合は終了
            if not consumption_settings.history_enabled:
                print("[DEBUG] History logging is disabled")
                return
                
            if not consumption_settings.history_channel_id:
                print("[DEBUG] No history channel configured")
                return

            # チャンネルの取得
            channel = self.bot.get_channel(int(consumption_settings.history_channel_id))
            print(f"[DEBUG] Using history channel: {consumption_settings.history_channel_id}")

            if not channel:
                print(f"[WARNING] History channel not found: {consumption_settings.history_channel_id}")
                return

            # 権限チェック
            bot_member = channel.guild.me
            channel_permissions = channel.permissions_for(bot_member)
            
            # 必要な権限のチェック
            if not channel_permissions.send_messages:
                print(f"[WARNING] Bot lacks 'Send Messages' permission in channel {channel.id}")
                return
                
            if not channel_permissions.embed_links:
                print(f"[WARNING] Bot lacks 'Embed Links' permission in channel {channel.id}")
                return

            # ログを送信
            point_unit = settings.global_settings.point_unit
            embed = discord.Embed(
                title="ポイント消費履歴",
                description=f"<@{history_data['user_id']}>が{history_data['points']}{point_unit}を消費しました",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )

            embed.add_field(
                name="承認者",
                value=f"<@{history_data['admin_id']}>",
                inline=True
            )

            await channel.send(embed=embed)

        except discord.Forbidden as e:
            print(f"[ERROR] Forbidden error while sending log: {e}")
            print(f"Bot lacks required permissions in channel {consumption_settings.history_channel_id}")
        except Exception as e:
            print(f"[ERROR] Error logging consumption: {e}")
            print(traceback.format_exc())

    def _parse_button_custom_id(self, custom_id: str) -> tuple:
        """ボタンのカスタムIDからユーザーID、ポイント、ユニットIDを抽出 - 改善版"""
        try:
            prefix = "approve_consume_" if "approve" in custom_id else "cancel_consume_"
            data = custom_id.replace(prefix, "").split('_')
            if len(data) != 3:
                raise ValueError(f"Invalid custom_id format: {custom_id}")
            user_id, points, unit_id = data
            return user_id, int(points), unit_id
        except Exception as e:
            print(f"[ERROR] Failed to parse custom_id {custom_id}: {e}")
            raise ValueError(f"Invalid custom_id format: {custom_id}")
    
class PointConsumptionModal(discord.ui.Modal):
    @classmethod
    async def get_latest_wallet_address(cls, bot, server_id: str, user_id: str) -> Optional[str]:
        """ユーザーの最新の承認済みウォレットアドレスを取得"""
        try:
            response = await asyncio.to_thread(
                bot.db.point_consumption_history_table.scan,
                FilterExpression='server_id = :sid AND user_id = :uid AND #status = :status AND attribute_exists(wallet_address)',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':sid': server_id,
                    ':uid': user_id,
                    ':status': 'approved'
                }
            )
            
            if not response.get('Items'):
                return None
                
            # タイムスタンプでソートして最新のウォレットアドレスを取得
            latest_record = sorted(
                response['Items'],
                key=lambda x: x['timestamp'],
                reverse=True
            )[0]
            
            return latest_record.get('wallet_address')
            
        except Exception as e:
            print(f"[ERROR] Failed to get wallet address: {e}")
            return None

    @classmethod
    async def create(cls, settings: ServerSettings, available_points: int, unit_id: str, interaction: discord.Interaction):
        """モーダルを非同期で作成するファクトリメソッド"""
        instance = cls(settings, available_points, unit_id)
        instance.interaction = interaction

        # 最新のウォレットアドレスを取得
        if instance.modal_settings.fields.get("wallet"):
            current_wallet = await cls.get_latest_wallet_address(
                interaction.client,
                str(interaction.guild_id),
                str(interaction.user.id)
            )
            if current_wallet:
                instance.wallet.default = current_wallet

        return instance
    
    def __init__(self, settings: ServerSettings, available_points: int, unit_id: str, interaction: discord.Interaction = None):
        """
        モーダルの初期化
        Args:
            settings (ServerSettings): サーバー設定（データベースから取得）
            available_points (int): 利用可能なポイント
            unit_id (str): ポイントユニットID
        Raises:
            ValueError: 設定が不正な場合
        """

        if not settings.point_consumption_settings.modal_settings.title:
            super().__init__(title="ポイント消費")  # デフォルトタイトル
        else:
            super().__init__(title=settings.point_consumption_settings.modal_settings.title)
        
        self.interaction = interaction

        # super().__init__(title=settings.point_consumption_settings.modal_settings.title)

        # 詳細な設定の検証とデバッグログ
        print("[DEBUG] === Modal Initialization Start ===")
        print(f"[DEBUG] Raw settings object: {settings}")
        
        # 基本設定の存在チェック
        if not settings:
            print("[ERROR] Settings object is None")
            raise ValueError("Server settings object is missing")

        if not settings.point_consumption_settings:
            print("[ERROR] Point consumption settings is None")
            raise ValueError("Point consumption settings is missing")

        if not hasattr(settings.point_consumption_settings, 'modal_settings'):
            print("[ERROR] Modal settings attribute is missing")
            raise ValueError("Modal settings is missing from point consumption settings")

        modal_settings = settings.point_consumption_settings.modal_settings
        print(f"[DEBUG] Modal settings object: {modal_settings}")

        # fields設定の詳細チェック
        if not hasattr(modal_settings, 'fields'):
            print("[ERROR] Fields attribute is missing from modal settings")
            raise ValueError("Fields configuration is missing from modal settings")

        print(f"[DEBUG] Modal fields configuration: {modal_settings.fields}")
        
        # wallet設定の詳細チェック
        if 'wallet' not in modal_settings.fields:
            print("[ERROR] Wallet field configuration is missing")
            raise ValueError("Wallet field is not configured in modal settings")

        print(f"[DEBUG] Wallet field configuration: {modal_settings.fields['wallet']}")
        
        # Point unit validation
        point_unit = next(
            (unit for unit in settings.global_settings.point_units if unit.unit_id == unit_id),
            None
        )
        if not point_unit:
            print("[ERROR] Invalid point unit ID")
            raise ValueError(f"Point unit with ID {unit_id} not found")

        # Modal initialization
        super().__init__(title=modal_settings.title)
        
        self.settings = settings
        self.modal_settings = modal_settings
        self.available_points = available_points
        self.point_consumption_settings = settings.point_consumption_settings
        self.unit_id = unit_id
        self.point_unit = point_unit

        # Points input field
        points_label = modal_settings.field_labels.get("points", "消費ポイント")
        points_placeholder = modal_settings.field_placeholders.get("points", "消費するポイント数を入力").format(
            max=available_points
        )

        self.points = discord.ui.TextInput(
            label=points_label,
            placeholder=points_placeholder,
            required=True,
            min_length=1,
            max_length=len(str(available_points))
        )
        self.add_item(self.points)
        
        # Wallet field validation and addition
        # Wallet field
        wallet_config = modal_settings.fields.get("wallet")
        if wallet_config is True:
            wallet_label = modal_settings.field_labels.get("wallet", "ウォレットアドレス")
            wallet_placeholder = modal_settings.field_placeholders.get("wallet", "0x...")
            
            self.wallet = discord.ui.TextInput(
                label=wallet_label,
                placeholder=wallet_placeholder,
                required=True,
                min_length=42,
                max_length=42
            )
            self.add_item(self.wallet)
        else:
            print(f"[ERROR] Invalid wallet field configuration: {wallet_config}")
            raise ValueError(f"Wallet field is configured incorrectly. Expected boolean True, got {wallet_config}")

        # Email field (keeping the existing logic)
        if modal_settings.fields.get("email"):
            email_label = modal_settings.field_labels.get("email", "メールアドレス")
            email_placeholder = modal_settings.field_placeholders.get("email", "example@example.com")
            
            self.email = discord.ui.TextInput(
                label=email_label,
                placeholder=email_placeholder,
                required=True
            )
            self.add_item(self.email)

        print("[DEBUG] === Modal Initialization Complete ===")

    async def initialize_wallet(self):
        """ウォレットアドレスの初期値を設定"""
        if self.interaction and hasattr(self, 'wallet'):
            current_wallet = await self.get_latest_wallet_address(
                self.interaction.client,
                str(self.interaction.guild_id),
                str(self.interaction.user.id)
            )
            if current_wallet:
                self.wallet.default = current_wallet

    async def on_submit(self, interaction: discord.Interaction):
            """フォーム送信時の処理"""
            try:
                # print(f"[DEBUG] Starting form submission for user {interaction.user.id}")

                # サーバー設定の再取得（最新の状態を確保）
                settings = await interaction.client.get_server_settings(str(interaction.guild_id))
                if not settings or not settings.point_consumption_settings:
                    print("[ERROR] Server settings not found during form submission")
                    await interaction.response.send_message(
                        "サーバー設定の取得に失敗しました。",
                        ephemeral=True
                    )
                    return

                modal_settings = settings.point_consumption_settings.modal_settings
                consumption_settings = settings.point_consumption_settings
                validation = modal_settings.validation
                print(f"[DEBUG] Validation settings: {validation}")

                # 利用可能ポイントの再確認
                available_points = await interaction.client.point_manager.get_points(
                    str(interaction.guild_id),
                    str(interaction.user.id),
                    self.unit_id  # unit_idを追加
                )
                print(f"[DEBUG] Available points for user {interaction.user.id}: {available_points}")

                # ポイントのバリデーション
                try:
                    points = int(self.points.value)
                except ValueError:
                    await interaction.response.send_message(
                        modal_settings.error_messages.get(
                            "invalid_points",
                            "無効なポイント値です。"
                        ),
                        ephemeral=True
                    )
                    return

                points_validation = validation.get("points", {"min": 0, "max": None})
                if points < points_validation["min"] or \
                (points_validation["max"] and points > points_validation["max"]):
                    await interaction.response.send_message(
                        modal_settings.error_messages.get(
                            "invalid_points",
                            "無効なポイント値です。"
                        ),
                        ephemeral=True
                    )
                    return

                # 利用可能ポイントの確認（消費なので、available_pointsから引いた後が0以上になるかチェック）
                if (available_points - points) < 0:
                    await interaction.response.send_message(
                        modal_settings.error_messages.get(
                            "insufficient_points",
                            f"利用可能なポイント({available_points})を超えています。"
                        ),
                        ephemeral=True
                    )
                    return

                # ウォレットアドレスのバリデーション
                wallet_address = None
                if hasattr(self, 'wallet'):
                    wallet_pattern = validation.get("wallet", {}).get("pattern", "^0x[a-fA-F0-9]{40}$")
                    if not re.match(wallet_pattern, self.wallet.value):
                        await interaction.response.send_message(
                            modal_settings.error_messages.get(
                                "invalid_wallet",
                                "無効なウォレットアドレスです。"
                            ),
                            ephemeral=True
                        )
                        return
                    wallet_address = self.wallet.value

                # メールアドレスのバリデーション
                email = None
                if hasattr(self, 'email'):
                    email_pattern = validation.get("email", {}).get("pattern", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
                    if not re.match(email_pattern, self.email.value):
                        await interaction.response.send_message(
                            modal_settings.error_messages.get(
                                "invalid_email",
                                "無効なメールアドレスです。"
                            ),
                            ephemeral=True
                        )
                        return
                    email = self.email.value

                # 申請データの作成
                timestamp = datetime.now(pytz.UTC).isoformat()
                request_data = {
                    'server_id': str(interaction.guild_id),
                    'timestamp': timestamp,
                    'user_id': str(interaction.user.id),
                    'points': points,
                    'wallet_address': wallet_address,
                    'email': email,
                    'thread_id': str(interaction.channel.id),
                    'status': 'pending',
                    'created_at': timestamp,
                    'unit_id': self.unit_id  # 追加
                }

                # リクエストデータ作成時のデバッグログ
                print(f"[DEBUG] Creating consumption request:")
                print(f"  server_id: {str(interaction.guild_id)}")
                print(f"  user_id: {str(interaction.user.id)}")
                print(f"  points: {points}")
                print(f"  unit_id: {self.unit_id}")
                print(f"  thread_id: {str(interaction.channel.id)}")
                print(f"  timestamp: {timestamp}")

                # 履歴の保存
                success = await interaction.client.db.save_consumption_history(request_data)
                if not success:
                    await interaction.response.send_message(
                        modal_settings.error_messages.get(
                            "save_error",
                            "申請の保存に失敗しました。"
                        ),
                        ephemeral=True
                    )
                    return

                print(f"[DEBUG] Save result: {success}")

                # 通知チャンネルの取得と設定
                target_channel = interaction.channel
                if consumption_settings.notification_channel_id:
                    notification_channel = interaction.guild.get_channel(
                        int(consumption_settings.notification_channel_id)
                    )
                    if notification_channel:
                        target_channel = notification_channel

                # 承認ボタンの作成
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label="承認",
                    style=discord.ButtonStyle.success,
                    custom_id=f"approve_consume_{interaction.user.id}_{self.points.value}_{self.unit_id}"
                ))
                view.add_item(discord.ui.Button(
                    label="キャンセル",
                    style=discord.ButtonStyle.danger,
                    custom_id=f"cancel_consume_{interaction.user.id}_{self.points.value}_{self.unit_id}"
                ))

                # メンションの準備
                mention_text = ""
                if consumption_settings.mention_role_ids:
                    mention_text = " ".join(f"<@&{role_id}>" for role_id in consumption_settings.mention_role_ids)
                    mention_text += "\n"

                # ログ記録
                if consumption_settings.logging_enabled and consumption_settings.logging_channel_id:
                    try:
                        log_channel = interaction.guild.get_channel(
                            int(consumption_settings.logging_channel_id)
                        )
                        if log_channel:
                            log_embed = discord.Embed(
                                title="ポイント消費申請",
                                description=f"{interaction.user.mention}が{points}{settings.global_settings.point_unit}の消費を申請しました。",
                                color=discord.Color.blue(),
                                timestamp=datetime.now()
                            )
                            if wallet_address:
                                log_embed.add_field(
                                    name="ウォレットアドレス",
                                    value=wallet_address,
                                    inline=False
                                )
                            if email:
                                log_embed.add_field(
                                    name="メールアドレス",
                                    value=email,
                                    inline=False
                                )
                            await log_channel.send(embed=log_embed)
                    except Exception as e:
                        print(f"[ERROR] Failed to send log: {e}")

                # 通知メッセージの送信
                notification_message = self.point_consumption_settings.notification_message.format(
                    user=interaction.user.mention,
                    points=self.points.value,
                    unit=self.point_unit.name  # point_unit.nameを使用
                )

                await target_channel.send(
                    f"{mention_text}{notification_message}",
                    view=view
                )

                # 完了メッセージ
                await interaction.response.send_message(
                    modal_settings.success_message or "申請を送信しました。",
                    ephemeral=True
                )

            except Exception as e:
                print(f"[ERROR] Error in modal submission: {e}")
                print(traceback.format_exc())
                await interaction.response.send_message(
                    modal_settings.error_messages.get(
                        "system_error",
                        "申請処理中にエラーが発生しました。"
                    ),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(PointsConsumption(bot))
