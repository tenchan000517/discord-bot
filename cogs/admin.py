import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
import traceback

from .settings.modals import GachaSettingsModal, BattleSettingsModal, FortuneSettingsModal, PointConsumptionSettingsModal
from .settings.views import SettingsView, FeatureSettingsView

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="サーバー設定を表示または変更します")
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction):
        """サーバー設定を管理するコマンド"""
        try:
            print(f"[INFO] settings command triggered by user: {interaction.user.id}, guild: {interaction.guild_id}")
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                print(f"[ERROR] No settings found for guild_id: {interaction.guild_id}")
                await interaction.response.send_message("設定の取得に失敗しました。", ephemeral=True)
                return

            print(f"[DEBUG] Retrieved settings type: {type(settings)}, content: {settings}")

            embed = self._create_settings_embed(settings)
            view = SettingsView(self.bot, settings)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            print(f"[ERROR] Exception in settings command: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定の取得中にエラーが発生しました。",
                ephemeral=True
            )

    def _create_settings_embed(self, settings) -> discord.Embed:
        """設定表示用のEmbedを作成"""
        embed = discord.Embed(
            title="🛠️ サーバー設定",
            color=discord.Color.blue()
        )

        # グローバル設定
        embed.add_field(
            name="グローバル設定",
            value=f"ポイント単位: {settings.global_settings.point_unit}\n"
                  f"タイムゾーン: {settings.global_settings.timezone}\n"
                  f"言語: {settings.global_settings.language}",
            inline=False
        )

        # 機能の有効/無効状態
        enabled_features = []
        for feature, enabled in settings.global_settings.features_enabled.items():
            status = "✅" if enabled else "❌"
            enabled_features.append(f"{feature}: {status}")
        
        embed.add_field(
            name="機能の状態",
            value="\n".join(enabled_features),
            inline=False
        )

        return embed

    @app_commands.command(
        name="feature",
        description="特定の機能の設定を管理します"
    )
    @app_commands.describe(
        feature="設定を変更する機能を選択",
        action="実行するアクション"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def feature_settings(
        self,
        interaction: discord.Interaction,
        feature: Literal["gacha", "battle", "fortune", "rewards", "point_consumption"],  # point_consumptionを追加
        action: Literal["view", "enable", "disable", "configure"]
    ):
        """機能ごとの詳細設定を管理"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                await interaction.response.send_message(
                    "設定の取得に失敗しました。",
                    ephemeral=True
                )
                return

            if action == "view":
                await self._show_feature_settings(interaction, settings, feature)
            elif action in ["enable", "disable"]:
                await self._toggle_feature(interaction, settings, feature, action == "enable")
            elif action == "configure":
                await self._show_feature_config(interaction, settings, feature)

        except Exception as e:
            print(f"Error in feature_settings command: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定の操作中にエラーが発生しました。",
                ephemeral=True
            )

    # リワード管理用のコマンドグループ
    rewards_group = app_commands.Group(
        name="rewards_admin",
        description="報酬システムの管理コマンド",
        default_permissions=discord.Permissions(administrator=True)
    )

    @rewards_group.command(
        name="view_settings",
        description="現在の報酬設定を表示します"
    )
    async def view_rewards_settings(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            reward_settings = settings.feature_settings.get('rewards', {})

            if not reward_settings:
                await interaction.followup.send("報酬設定が見つかりません。", ephemeral=True)
                return

            embed = discord.Embed(
                title="報酬システム設定",
                color=discord.Color.blue()
            )

            # Web3設定
            web3 = reward_settings.get('web3', {})
            web3_status = "✅" if web3.get('rpc_url') and web3.get('private_key') else "❌"
            embed.add_field(
                name="Web3設定",
                value=f"設定状態: {web3_status}\n"
                      f"NFTコントラクト: `{web3.get('nft_contract_address', 'なし')}`\n"
                      f"トークンコントラクト: `{web3.get('token_contract_address', 'なし')}`",
                inline=False
            )

            # クーポンAPI設定
            api = reward_settings.get('coupon_api', {})
            api_status = "✅" if api.get('api_url') and api.get('api_key') else "❌"
            embed.add_field(
                name="クーポンAPI設定",
                value=f"設定状態: {api_status}\n"
                      f"API URL: `{api.get('api_url', 'なし')}`",
                inline=False
            )

            # 制限値設定
            limits = reward_settings.get('limits', {})
            embed.add_field(
                name="制限値設定",
                value=f"クーポン交換: {limits.get('min_points_coupon', '?')}～{limits.get('max_points_coupon', '?')}ポイント\n"
                      f"NFT発行: {limits.get('min_points_nft', '?')}ポイント以上\n"
                      f"トークン交換: {limits.get('min_points_token', '?')}ポイント以上\n"
                      f"トークン変換レート: {limits.get('token_conversion_rate', '?')}",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in view_settings: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("エラーが発生しました。", ephemeral=True)

    @rewards_group.command(
        name="set_web3",
        description="Web3の設定を行います"
    )
    @app_commands.describe(
        rpc_url="Web3のRPCエンドポイントURL",
        nft_contract="NFTコントラクトのアドレス",
        token_contract="トークンコントラクトのアドレス"
    )
    async def set_web3(
        self,
        interaction: discord.Interaction,
        rpc_url: str,
        nft_contract: str,
        token_contract: str
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not hasattr(settings, 'feature_settings'):
                settings.feature_settings = {}
            if 'rewards' not in settings.feature_settings:
                settings.feature_settings['rewards'] = {
                    'enabled': True,
                    'web3': {},
                    'coupon_api': {},
                    'limits': {}
                }

            settings.feature_settings['rewards']['web3'].update({
                'rpc_url': rpc_url,
                'nft_contract_address': nft_contract,
                'token_contract_address': token_contract
            })

            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.followup.send(
                    "Web3設定を更新しました。\n"
                    "⚠️ プライベートキーは `/rewards_admin set_private_key` で別途設定してください。",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("設定の更新に失敗しました。", ephemeral=True)

        except Exception as e:
            print(f"Error in set_web3: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("エラーが発生しました。", ephemeral=True)

    @rewards_group.command(
        name="set_private_key",
        description="Web3のプライベートキーを設定します"
    )
    @app_commands.describe(
        private_key="Web3のプライベートキー"
    )
    async def set_private_key(
        self,
        interaction: discord.Interaction,
        private_key: str
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            settings.feature_settings['rewards']['web3']['private_key'] = private_key

            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.followup.send(
                    "プライベートキーを設定しました。\n"
                    "⚠️ このキーは安全に保管されます。",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("設定の更新に失敗しました。", ephemeral=True)

        except Exception as e:
            print(f"Error in set_private_key: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("エラーが発生しました。", ephemeral=True)

    @rewards_group.command(
        name="set_coupon_api",
        description="クーポンAPIの設定を行います"
    )
    @app_commands.describe(
        api_url="クーポンAPIのエンドポイントURL",
        api_key="クーポンAPIのAPIキー"
    )
    async def set_coupon_api(
        self,
        interaction: discord.Interaction,
        api_url: str,
        api_key: str
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            settings.feature_settings['rewards']['coupon_api'].update({
                'api_url': api_url,
                'api_key': api_key
            })

            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.followup.send("クーポンAPI設定を更新しました。", ephemeral=True)
            else:
                await interaction.followup.send("設定の更新に失敗しました。", ephemeral=True)

        except Exception as e:
            print(f"Error in set_coupon_api: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("エラーが発生しました。", ephemeral=True)

    @rewards_group.command(
        name="set_limits",
        description="報酬交換の制限値を設定します"
    )
    @app_commands.describe(
        min_points_coupon="クーポン交換の最小ポイント",
        max_points_coupon="クーポン交換の最大ポイント",
        min_points_nft="NFT発行の最小ポイント",
        min_points_token="トークン交換の最小ポイント",
        token_conversion_rate="トークン変換レート"
    )
    async def set_limits(
        self,
        interaction: discord.Interaction,
        min_points_coupon: int,
        max_points_coupon: int,
        min_points_nft: int,
        min_points_token: int,
        token_conversion_rate: float
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if min_points_coupon > max_points_coupon:
                await interaction.followup.send(
                    "クーポンの最小ポイントが最大ポイントを超えています。",
                    ephemeral=True
                )
                return

            if token_conversion_rate <= 0 or token_conversion_rate > 1:
                await interaction.followup.send(
                    "トークン変換レートは0より大きく1以下である必要があります。",
                    ephemeral=True
                )
                return

            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            settings.feature_settings['rewards']['limits'].update({
                'min_points_coupon': min_points_coupon,
                'max_points_coupon': max_points_coupon,
                'min_points_nft': min_points_nft,
                'min_points_token': min_points_token,
                'token_conversion_rate': token_conversion_rate
            })

            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.followup.send("報酬制限値を更新しました。", ephemeral=True)
            else:
                await interaction.followup.send("設定の更新に失敗しました。", ephemeral=True)

        except Exception as e:
            print(f"Error in set_limits: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("エラーが発生しました。", ephemeral=True)

    def _create_feature_embed(self, feature: str, settings, embed: discord.Embed) -> discord.Embed:
        """機能ごとの設定Embedを作成"""
        if feature == "gacha":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}\n"
                      f"アイテム数: {len(settings.items)}",
                inline=False
            )
            if settings.messages:
                embed.add_field(
                    name="メッセージ設定",
                    value="カスタマイズ済み",
                    inline=False
                )
        elif feature == "battle":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}\n"
                      f"キルポイント: {settings.points_per_kill}\n"
                      f"優勝ポイント: {settings.winner_points}",
                inline=False
            )
        elif feature == "fortune":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}",
                inline=False
            )
        elif feature == "rewards":
            reward_settings = getattr(settings, 'feature_settings', {}).get('rewards', {})
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if reward_settings.get('enabled', False) else '無効'}",
                inline=False
            )
            
            # Web3設定の状態
            web3 = reward_settings.get('web3', {})
            web3_status = "✅" if web3.get('rpc_url') and web3.get('private_key') else "❌"
            embed.add_field(
                name="Web3設定",
                value=f"設定状態: {web3_status}",
                inline=True
            )
            
            # クーポンAPI設定の状態
            api = reward_settings.get('coupon_api', {})
            api_status = "✅" if api.get('api_url') and api.get('api_key') else "❌"
            embed.add_field(
                name="クーポンAPI",
                value=f"設定状態: {api_status}",
                inline=True
            )
        elif feature == "point_consumption":
            point_settings = settings.point_consumption_settings
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if point_settings.enabled else '無効'}\n"
                      f"ボタン名: {point_settings.button_name}\n"
                      f"必要ポイント: {point_settings.required_points}",
                inline=False
            )
            if point_settings.logging_enabled:
                embed.add_field(
                    name="ログ設定",
                    value="有効",
                    inline=False
                )

        return embed

    async def _toggle_feature(
        self,
        interaction: discord.Interaction,
        settings,
        feature: str,
        enable: bool
    ):
        """機能の有効/無効を切り替え"""
        settings.global_settings.features_enabled[feature] = enable
        success = await self.bot.settings_manager.update_settings(
            str(interaction.guild_id),
            settings
        )

        if success:
            await interaction.response.send_message(
                f"{feature.capitalize()}機能を{'有効' if enable else '無効'}にしました。",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "設定の更新に失敗しました。",
                ephemeral=True
            )

    async def _show_feature_config(
        self,
        interaction: discord.Interaction,
        settings,
        feature: str
    ):
        """機能の詳細設定画面を表示"""
        try:
            if feature == "rewards":
                # 報酬設定の場合は専用のコマンドを使用するよう案内
                await interaction.response.send_message(
                    "報酬機能の詳細設定は `/rewards_admin` コマンドグループを使用してください。\n"
                    "例: `/rewards_admin view_settings`, `/rewards_admin set_web3`, etc.",
                    ephemeral=True
                )
                return

            modal_class = {
                'gacha': GachaSettingsModal,
                'battle': BattleSettingsModal,
                'fortune': FortuneSettingsModal,
                'point_consumption': PointConsumptionSettingsModal  # 追加
            }.get(feature)

            if modal_class:
                feature_settings = getattr(settings, f"{feature}_settings")
                modal = modal_class(feature_settings, self.bot.settings_manager)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message(
                    "無効な機能が指定されました。",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error showing feature config: {e}")
            await interaction.response.send_message(
                "設定画面の表示中にエラーが発生しました。",
                ephemeral=True
            )

    # cogs/admin.py の既存のclassに追加

    @app_commands.command(
        name="setup_consumption",
        description="ポイント消費パネルを設置"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_consumption(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        """ポイント消費パネルのセットアップ"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings or not settings.point_consumption_settings:
                await interaction.response.send_message(
                    "ポイント消費機能が設定されていません。",
                    ephemeral=True
                )
                return

            point_consumption_cog = self.bot.get_cog('PointsConsumption')
            if not point_consumption_cog:
                await interaction.response.send_message(
                    "ポイント消費機能が利用できません。",
                    ephemeral=True
                )
                return

            await point_consumption_cog.setup_consumption_panel(
                str(channel.id),
                settings.point_consumption_settings
            )

            await interaction.response.send_message(
                f"ポイント消費パネルを{channel.mention}に設置しました。",
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in setup_consumption: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定中にエラーが発生しました。",
                ephemeral=True
            )

    # 消費機能設定用のコマンドグループを作成
    consumption_group = app_commands.Group(
        name="consumption",
        description="ポイント消費機能の設定",
        default_permissions=discord.Permissions(administrator=True)
    )

    @consumption_group.command(
        name="settings",
        description="ポイント消費の設定を変更"
    )
    @app_commands.describe(
        button_name="ボタンの表示名",
        channel="パネルを表示するチャンネル",
        notification_channel="通知を送信するチャンネル",
        required_points="必要ポイント数",
        use_thread="専用スレッドを使用するか",
        completion_message="完了メッセージを表示するか"
    )
    async def consumption_settings(
        self,
        interaction: discord.Interaction,
        button_name: str = None,
        channel: discord.TextChannel = None,
        notification_channel: discord.TextChannel = None,
        required_points: int = None,
        use_thread: bool = None,
        completion_message: bool = None
    ):
        """ポイント消費機能の設定を変更"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                await interaction.response.send_message(
                    "サーバー設定が見つかりません。",
                    ephemeral=True
                )
                return

            # 現在の設定を取得
            point_consumption_settings = settings.point_consumption_settings or PointConsumptionSettings()

            # 変更された項目のみ更新
            if button_name is not None:
                point_consumption_settings.button_name = button_name
            if channel is not None:
                point_consumption_settings.channel_id = str(channel.id)
            if notification_channel is not None:
                point_consumption_settings.notification_channel_id = str(notification_channel.id)
            if required_points is not None:
                point_consumption_settings.required_points = required_points
            if use_thread is not None:
                point_consumption_settings.use_thread = use_thread
            if completion_message is not None:
                point_consumption_settings.completion_message_enabled = completion_message

            # 設定を保存
            settings.point_consumption_settings = point_consumption_settings
            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.response.send_message(
                    "設定を更新しました。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error in consumption_settings: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定中にエラーが発生しました。",
                ephemeral=True
            )

    @consumption_group.command(
        name="mentions",
        description="通知時のメンションを設定"
    )
    async def consumption_mentions(
        self,
        interaction: discord.Interaction,
        roles: str
    ):
        """通知時のメンションロールを設定"""
        try:
            # カンマ区切りのロールIDを解析
            role_ids = [rid.strip() for rid in roles.split(',')]
            
            # ロールの存在チェック
            invalid_roles = []
            for role_id in role_ids:
                role = interaction.guild.get_role(int(role_id))
                if not role:
                    invalid_roles.append(role_id)

            if invalid_roles:
                await interaction.response.send_message(
                    f"以下のロールIDが無効です: {', '.join(invalid_roles)}",
                    ephemeral=True
                )
                return

            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                await interaction.response.send_message(
                    "サーバー設定が見つかりません。",
                    ephemeral=True
                )
                return

            # メンションロールを更新
            settings.point_consumption_settings.mention_role_ids = role_ids
            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.response.send_message(
                    "メンション設定を更新しました。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )

        except ValueError:
            await interaction.response.send_message(
                "無効なロールIDの形式です。正しいロールIDをカンマ区切りで入力してください。",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in consumption_mentions: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定中にエラーが発生しました。",
                ephemeral=True
            )

    @consumption_group.command(
        name="logging",
        description="ログ設定を変更"
    )
    @app_commands.describe(
        enabled="ログ機能を有効にするか",
        channel="ログを送信するチャンネル",
        actions="記録するアクション（click,complete,cancel,all）"
    )
    async def consumption_logging(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        channel: discord.TextChannel = None,
        actions: str = None
    ):
        """ログ設定を変更"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                await interaction.response.send_message(
                    "サーバー設定が見つかりません。",
                    ephemeral=True
                )
                return

            # ログ設定を更新
            settings.point_consumption_settings.logging_enabled = enabled
            if channel:
                settings.point_consumption_settings.logging_channel_id = str(channel.id)
            
            if actions:
                valid_actions = ['click', 'complete', 'cancel', 'all']
                action_list = [a.strip() for a in actions.split(',')]
                
                if 'all' in action_list:
                    action_list = ['click', 'complete', 'cancel']
                
                invalid_actions = [a for a in action_list if a not in valid_actions]
                if invalid_actions:
                    await interaction.response.send_message(
                        f"無効なアクション: {', '.join(invalid_actions)}",
                        ephemeral=True
                    )
                    return
                
                settings.point_consumption_settings.logging_actions = action_list

            success = await self.bot.settings_manager.update_settings(
                str(interaction.guild_id),
                settings
            )

            if success:
                await interaction.response.send_message(
                    "ログ設定を更新しました。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error in consumption_logging: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定中にエラーが発生しました。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Admin(bot))