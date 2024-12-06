# main.py
import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from utils.mongo_database import MongoDatabase  # クラス名を変更

load_dotenv()

# 環境変数の読み込み
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/discord_bot')  # MongoDB接続URI追加

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
        self.db = MongoDatabase()  # クラス名の変更のみ

    async def setup_hook(self):
        try:
            await self.load_extension('cogs.gacha')
        except Exception as e:
            print(f"Failed to load extensions: {e}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is ready in {len(self.guilds)} servers.')

async def main():
    bot = GachaBot()
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())