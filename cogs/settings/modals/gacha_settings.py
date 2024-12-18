import discord
from .base import BaseSettingsModal
from models.server_settings import MessageSettings, MediaSettings

class GachaSettingsModal(BaseSettingsModal):
    """ガチャ設定モーダル"""
    def __init__(self, settings, settings_manager):
        super().__init__(title="ガチャ設定", settings=settings)
        self.settings_manager = settings_manager

        # デフォルト設定を定義
        self.default_messages = {
            'setup': 'ガチャへようこそ！\nここではさまざまなアイテムを獲得できます。',
            'daily': '{user}さんがガチャを引きました！',
            'win': 'おめでとうございます！{item}を獲得しました！',
            'custom_messages': {}
        }
        self.default_media = {
            'setup_image': None,
            'banner_gif': None
        }

        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        try:
            # 既存の設定またはデフォルト値を取得
            current_messages = settings.messages or MessageSettings(**self.default_messages)
            current_media = settings.media or MediaSettings(**self.default_media)

            # None チェックを追加
            setup_default = (current_messages.setup or self.default_messages['setup']) if current_messages else self.default_messages['setup']
            daily_default = (current_messages.daily or self.default_messages['daily']) if current_messages else self.default_messages['daily']
            win_default = (current_messages.win or self.default_messages['win']) if current_messages else self.default_messages['win']
            banner_default = (current_media.banner_gif or '') if current_media else ''

            self.setup_message = discord.ui.TextInput(
                label="セットアップメッセージ",
                style=discord.TextStyle.paragraph,
                placeholder="ガチャ初期設定時のメッセージ",
                required=False,
                default=setup_default,
                max_length=1000
            )
            self.add_item(self.setup_message)

            self.daily_message = discord.ui.TextInput(
                label="デイリーメッセージ",
                style=discord.TextStyle.paragraph,
                placeholder="ガチャ実行時のメッセージ ({user}でメンション)",
                required=False,
                default=daily_default,
                max_length=1000
            )
            self.add_item(self.daily_message)

            self.win_message = discord.ui.TextInput(
                label="当選メッセージ",
                style=discord.TextStyle.paragraph,
                placeholder="ガチャ当選時のメッセージ ({user}でメンション, {item}でアイテム名)",
                required=False,
                default=win_default,
                max_length=1000
            )
            self.add_item(self.win_message)

            self.banner_url = discord.ui.TextInput(
                label="バナー画像URL",
                placeholder="https://example.com/image.png",
                required=False,
                default=banner_default,
                max_length=200
            )
            self.add_item(self.banner_url)

        except Exception as e:
            print(f"[ERROR] Failed to setup fields: {e}")
            # デフォルト値を使用してフィールドをセットアップ
            self._setup_default_fields()

    def _setup_default_fields(self):
        """デフォルト値でフィールドをセットアップ"""
        self.setup_message = discord.ui.TextInput(
            label="セットアップメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ初期設定時のメッセージ",
            required=False,
            default=self.default_messages['setup'],
            max_length=1000
        )
        self.add_item(self.setup_message)

        self.daily_message = discord.ui.TextInput(
            label="デイリーメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ実行時のメッセージ ({user}でメンション)",
            required=False,
            default=self.default_messages['daily'],
            max_length=1000
        )
        self.add_item(self.daily_message)

        self.win_message = discord.ui.TextInput(
            label="当選メッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ当選時のメッセージ ({user}でメンション, {item}でアイテム名)",
            required=False,
            default=self.default_messages['win'],
            max_length=1000
        )
        self.add_item(self.win_message)

        self.banner_url = discord.ui.TextInput(
            label="バナー画像URL",
            placeholder="https://example.com/image.png",
            required=False,
            default='',
            max_length=200
        )
        self.add_item(self.banner_url)

    async def on_submit(self, interaction: discord.Interaction):
        """モーダル送信時の処理"""
        try:
            # URLのバリデーション
            if self.banner_url.value:
                is_valid, error_msg = await self._validate_url(self.banner_url.value)
                if not is_valid:
                    await interaction.response.send_message(error_msg, ephemeral=True)
                    return

            # 更新する設定を生成
            updated_settings = await self._create_updated_settings()

            # 設定を保存
            success = await self._update_feature_settings(interaction, 'gacha', updated_settings)
            
            if success:
                await interaction.response.send_message(
                    "✅ ガチャの設定を更新しました。\n\n"
                    f"セットアップメッセージ: {self.setup_message.value[:50]}...\n"
                    f"デイリーメッセージ: {self.daily_message.value[:50]}...\n"
                    f"当選メッセージ: {self.win_message.value[:50]}...",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ 設定の更新に失敗しました。\n"
                    "しばらく待ってから再度お試しください。",
                    ephemeral=True
                )

        except Exception as e:
            print(f"[ERROR] Error in on_submit: {str(e)}")
            await interaction.response.send_message(
                "❌ エラーが発生しました。\n"
                "しばらく待ってから再度お試しください。",
                ephemeral=True
            )

    async def _create_updated_settings(self) -> dict:
        """更新された設定を作成"""
        return {
            'enabled': self.settings.enabled,
            'messages': {
                'setup': self.setup_message.value,
                'daily': self.daily_message.value,
                'win': self.win_message.value,
                'custom_messages': self.settings.messages.custom_messages if self.settings.messages else {}
            },
            'media': {
                'banner_gif': self.banner_url.value
            },
            'items': self.settings.items or []
        }

    async def _update_feature_settings(self, interaction: discord.Interaction, feature: str, updated_settings: dict) -> bool:
        """機能の設定をDynamoDBに保存"""
        try:
            server_id = str(interaction.guild_id)
            print(f"[INFO] Updating {feature} settings for server_id: {server_id}")
            print(f"[DEBUG] Updated settings: {updated_settings}")

            # settings_managerのupdate_feature_settingsを呼び出す
            success = await self.settings_manager.update_feature_settings(server_id, feature, updated_settings)
            
            if not success:
                print(f"[ERROR] Failed to update {feature} settings in the database")
                return False

            return True
        except Exception as e:
            print(f"[ERROR] Failed to update {feature} settings: {e}")
            return False

    async def _validate_url(self, url: str) -> tuple:
        """URLのバリデーション"""
        if not url:  # 空のURLは許可
            return True, None
        if url.startswith(("http://", "https://")):
            return True, None
        return False, "無効なURLです。http://またはhttps://で始まるURLを指定してください。"