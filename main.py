# main.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from utils.aws_database import AWSDatabase
from utils.settings_manager import ServerSettingsManager
from utils.point_manager import PointManager
from utils.reward_manager import RewardManager

import traceback

load_dotenv()

# 環境変数の読み込み
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class GachaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=commands.DefaultHelpCommand(
                no_category='Commands'
            )
        )
        # キャッシュの初期化
        self.cache = {}
        
        # データベース接続試行
        try:
            # コアコンポーネントの初期化
            self.db = AWSDatabase()
            self.settings_manager = ServerSettingsManager(self.db)
            self.point_manager = PointManager(self)
            self.db_available = True
            print("Core database components initialized successfully")

            # オプショナルコンポーネントの初期化
            try:
                self.reward_manager = RewardManager(self)
                print("Reward manager initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize reward manager: {e}")
                self.reward_manager = None

        except Exception as e:
            print(f"Failed to initialize core database: {e}")
            print(traceback.format_exc())
            self.db_available = False

    async def setup_hook(self):
        extension_status = []
        try:
            # 管理コマンドを読み込み
            try:
                await self.load_extension('cogs.admin')
                print("Loaded admin extension")
                extension_status.append("Admin: ✅")
            except Exception as e:
                print(f"Failed to load admin extension: {e}")
                print(traceback.format_exc())
                extension_status.append("Admin: ❌")

            # 既存の拡張機能を読み込み
            for ext in ['gacha', 'fortunes', 'battle', 'automation', 'rewards', 'points_consumption']:  # points_consumptionを追加
                try:
                    await self.load_extension(f'cogs.{ext}')
                    print(f"Loaded {ext} extension")
                    extension_status.append(f"{ext.capitalize()}: ✅")
                except Exception as e:
                    print(f"Failed to load {ext} extension: {e}")
                    print(traceback.format_exc())
                    extension_status.append(f"{ext.capitalize()}: ❌")

            print("Extension loading completed")
            print("\n".join(extension_status))

            # スラッシュコマンドを同期
            print("Starting global command sync...")
            await self.tree.sync()
            print("Command sync completed")
            
            commands = await self.tree.fetch_commands()
            for cmd in commands:
                print(f" - /{cmd.name}")

        except Exception as e:
            print(f"Critical error in setup_hook: {e}")
            print(traceback.format_exc())

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is ready in {len(self.guilds)} servers.')
        print(f"Database status: {'Available' if self.db_available else 'Unavailable'}")

        # 全サーバーの設定をデバッグ出力（必要ならループする）
        for guild in self.guilds:
            print(f"[DEBUG] Loading settings for guild {guild.name} (ID: {guild.id})")
            settings = await self.get_server_settings(str(guild.id))
            if settings:
                print(f"[DEBUG] settings for {guild.id}: {settings}")
            else:
                print(f"[DEBUG] No settings found for guild {guild.id}")


    async def get_server_settings(self, guild_id: str):
        """サーバー設定を取得するヘルパーメソッド"""
        print(f"[DEBUG] 取得するサーバーID: {guild_id}")

        if not self.db_available:
            print("[DEBUG] Database is unavailable.")
            return None

        try:
            settings = await self.settings_manager.get_settings(str(guild_id))
            print(f"[DEBUG] settings: {settings}")

            # gacha_settings の抽出
            gacha_settings = settings.gacha_settings if settings else None
            print(f"[DEBUG] gacha_settings: {gacha_settings}")

            return settings
        except Exception as e:
            print(f"[ERROR] Error retrieving server settings for guild {guild_id}: {e}")
            print(traceback.format_exc())
            return None

            
    # main.py内のGachaBotクラスに追加

    async def on_guild_join(self, guild):
        """新しいサーバーに参加した時の処理"""
        try:
            # データベースが利用可能か確認
            if not self.db_available:
                print(f"Warning: Database unavailable. Could not register server {guild.id}")
                return

            # サーバーIDを登録
            await self.db.register_server(str(guild.id))
            print(f"Successfully registered new server: {guild.name} (ID: {guild.id})")

            # 初期設定も同時に作成（必要に応じて）
            await self.settings_manager.create_default_settings(str(guild.id))
            print(f"Created default settings for server: {guild.name}")

        except Exception as e:
            print(f"Error registering new server {guild.id}: {e}")
            print(traceback.format_exc())

    async def on_guild_remove(self, guild):
        """サーバーから削除された時の処理"""
        try:
            if not self.db_available:
                print(f"Warning: Database unavailable. Could not remove server {guild.id}")
                return

            # サーバーIDを削除（オプション）
            await self.db.remove_server(str(guild.id))
            print(f"Successfully removed server: {guild.name} (ID: {guild.id})")

        except Exception as e:
            print(f"Error removing server {guild.id}: {e}")
            print(traceback.format_exc())

async def main():
    try:
        bot = GachaBot()
        async with bot:
            await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Main loop error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())