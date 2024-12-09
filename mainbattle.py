import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from utils.aws_database import AWSDatabase
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
        # データベース接続試行
        try:
            self.db = AWSDatabase()
            print("Database initialized successfully")
            self.db_available = True
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            print(traceback.format_exc())
            self.db_available = False

    async def setup_hook(self):
        extension_status = []
        try:
            # ガチャ機能を読み込み
            try:
                await self.load_extension('cogs.gacha')
                print("Loaded gacha extension")
                extension_status.append("Gacha: ✅")
            except Exception as e:
                print(f"Failed to load gacha extension: {e}")
                print(traceback.format_exc())
                extension_status.append("Gacha: ❌")

            # 占い機能を読み込み
            try:
                await self.load_extension('cogs.fortunes')
                print("Loaded fortunes extension")
                extension_status.append("Fortunes: ✅")
            except Exception as e:
                print(f"Failed to load fortunes extension: {e}")
                print(traceback.format_exc())
                extension_status.append("Fortunes: ❌")

            # バトルロイヤル機能を読み込み
            try:
                await self.load_extension('cogs.battle')
                print("Loaded battle extension")
                extension_status.append("Battle: ✅")
            except Exception as e:
                print(f"Failed to load battle extension: {e}")
                print(traceback.format_exc())
                extension_status.append("Battle: ❌")

            print("Extension loading completed")
            print("\n".join(extension_status))

            # スラッシュコマンドを同期
            print("Starting global command sync...")
            await self.tree.sync()  # グローバルコマンドの同期
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