# main.py
import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from utils.aws_database import AWSDatabase

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
        self.db = AWSDatabase()

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

    # my_token = os.environ['DISCORD_BOT_TOKEN']
