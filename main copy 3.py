import discord
from discord.ext import commands
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
            print(f"Warning: Database initialization failed: {e}")
            print(traceback.format_exc())
            self.db = None
            self.db_available = False
            
        # テスト用フラグ
        self.test_mode = False

        # コマンド登録
        self.add_command(self.list_commands)
        self.add_command(self.sync_commands)
        self.add_command(self.test_command)

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
                extension_status.append("Gacha: ❌")

            # 占い機能を読み込み
            try:
                await self.load_extension('cogs.fortunes')
                print("Loaded fortunes extension")
                extension_status.append("Fortunes: ✅")
            except Exception as e:
                print(f"Failed to load fortunes extension: {e}")
                extension_status.append("Fortunes: ❌")

            # ランブル機能を読み込み
            try:
                await self.load_extension('cogs.rumble')
                print("Loaded rumble extension")
                extension_status.append("Rumble: ✅")
            except Exception as e:
                print(f"Failed to load rumble extension: {e}")
                extension_status.append("Rumble: ❌")

            print("Extension loading completed")
            print("\n".join(extension_status))

        except Exception as e:
            print(f"Critical error in setup_hook: {e}")
            print(traceback.format_exc())

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is ready in {len(self.guilds)} servers.')
        print(f"Database status: {'Available' if self.db_available else 'Unavailable'}")
        print(f"Registered text commands: {self.commands}")

        # スラッシュコマンドを同期（タイムアウトを設定）
        try:
            print("Starting command sync...")
            await asyncio.wait_for(self.tree.sync(), timeout=10.0)  # 10秒のタイムアウトを設定
            print("Command sync completed")
        except asyncio.TimeoutError:
            print("Command sync timed out")
        except Exception as e:
            print(f"Command sync failed: {e}")
            print(traceback.format_exc())

        # データベース接続テスト（利用可能な場合のみ）
        if self.db_available:
            try:
                test_server_id = self.guilds[0].id if self.guilds else "test_server"
                test_settings = self.db.get_server_settings(test_server_id)
                print(f"Database connection test: {test_settings}")
            except Exception as e:
                print(f"Database connection test failed: {e}")
                print(traceback.format_exc())
                self.db_available = False

    # データベース状態確認用のユーティリティメソッド
    def check_db_available(self):
        """データベースが利用可能かチェックし、状態を更新"""
        if not self.db_available or self.db is None:
            return False
        
        try:
            # 簡単な接続テスト
            test_settings = self.db.get_server_settings("test")
            return True
        except Exception:
            self.db_available = False
            return False

    # テストモード切り替えコマンド
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def test_mode(self, ctx, mode: str = None):
        """テストモードの切り替え (on/off)"""
        if mode and mode.lower() in ['on', 'true', '1']:
            self.test_mode = True
            await ctx.send("テストモードをONにしました。メンションは送信されません。")
        elif mode and mode.lower() in ['off', 'false', '0']:
            self.test_mode = False
            await ctx.send("テストモードをOFFにしました。通常の動作に戻ります。")
        else:
            current_mode = "ON" if self.test_mode else "OFF"
            await ctx.send(f"現在のテストモード: {current_mode}")

    # メッセージ送信をオーバーライド
    async def send_or_test(self, ctx, content=None, **kwargs):
        """テストモードに応じてメッセージを送信"""
        if self.test_mode:
            # メンションを削除
            if content:
                content = content.replace('@', '')
            if 'embed' in kwargs and kwargs['embed']:
                # Embedからメンションを削除
                if kwargs['embed'].description:
                    kwargs['embed'].description = kwargs['embed'].description.replace('@', '')
                for field in kwargs['embed'].fields:
                    field.value = field.value.replace('@', '')
                    field.name = field.name.replace('@', '')

        return await ctx.send(content, **kwargs)

    # スラッシュコマンドをリスト表示
    @commands.command()
    async def list_commands(self, ctx):
        """現在登録されているスラッシュコマンドをリスト表示します"""
        try:
            commands = await self.tree.fetch_commands()
            command_names = [command.name for command in commands]
            await ctx.send(f"Registered commands: {', '.join(command_names) or 'None'}")
        except Exception as e:
            await ctx.send(f"Failed to fetch commands: {e}")
            print(traceback.format_exc())

    # スラッシュコマンドを手動同期
    @commands.command()
    async def sync_commands(self, ctx):
        """スラッシュコマンドを手動で同期します"""
        try:
            await self.tree.sync()
            await ctx.send("スラッシュコマンドを同期しました！")
        except Exception as e:
            await ctx.send(f"Failed to sync commands: {e}")
            print(traceback.format_exc())

    # データベース状態確認コマンド
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def db_status(self, ctx):
        """データベースの状態を確認します"""
        is_available = self.check_db_available()
        await ctx.send(f"データベース状態: {'利用可能' if is_available else '利用不可'}")

    @commands.command()
    async def test_command(self, ctx):
        await ctx.send("Hello! This is a test.")

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