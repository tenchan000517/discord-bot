# main.py
import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from utils.aws_database import AWSDatabase
import traceback  # 追加

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
        try:
            self.db = AWSDatabase()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            print(traceback.format_exc())  # スタックトレースを出力

    async def setup_hook(self):
        try:
            await self.load_extension('cogs.gacha')
            print("Extensions loaded successfully")
        except Exception as e:
            print(f"Failed to load extensions: {e}")
            print(traceback.format_exc())  # スタックトレースを出力

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is ready in {len(self.guilds)} servers.')
        
        # テスト用のデータベース接続確認
        try:
            test_server_id = self.guilds[0].id if self.guilds else "test_server"
            test_settings = self.db.get_server_settings(test_server_id)
            print(f"Database connection test: {test_settings}")
        except Exception as e:
            print(f"Database connection test failed: {e}")
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