# main.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from utils.aws_database import AWSDatabase
from utils.settings_manager import ServerSettingsManager
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
            self.db = AWSDatabase()
            self.settings_manager = ServerSettingsManager(self.db)
            print("Database and Settings Manager initialized successfully")
            self.db_available = True
        except Exception as e:
            print(f"Failed to initialize database: {e}")
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
            for ext in ['gacha', 'fortunes', 'battle']:
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

    async def get_server_settings(self, guild_id: str):
        """サーバー設定を取得するヘルパーメソッド"""
        if not self.db_available:
            return None
        return await self.settings_manager.get_settings(str(guild_id))  # awaitを追加

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