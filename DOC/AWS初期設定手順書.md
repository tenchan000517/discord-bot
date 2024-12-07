# Discord Gacha Bot セットアップ手順書

## 1. AWSの初期設定

```bash
# 1.1 IAMユーザーの作成
1. AWSマネジメントコンソールにログイン
2. 上部の検索バーで「IAM」を検索しIAMダッシュボードに移動
3. 左メニューから「ユーザー」を選択
4. 「ユーザーを作成」をクリック
5. ユーザー名入力（例：discord-bot-user）
6. アクセスキーの作成にチェック
7. 「次へ」をクリック
8. 「ポリシーを直接アタッチ」を選択し、以下にチェック：
   - AWSLambdaFullAccess
   - AmazonDynamoDBFullAccess
   - CloudWatchFullAccess
9. 「次へ」→「ユーザーの作成」
10. 表示される認証情報を保存：
    - AWS_ACCESS_KEY_ID=AKIA...
    - AWS_SECRET_ACCESS_KEY=abcd...
```

```bash
# 1.2 DynamoDBテーブルの作成
1. AWSマネジメントコンソールで「DynamoDB」を検索
2. 「テーブルを作成」をクリック

# discord_usersテーブル
テーブル名: discord_users
パーティションキー: user_id (文字列)
デフォルト設定を使用
キャパシティモード: オンデマンド
「テーブルを作成」をクリック

# gacha_historyテーブル
テーブル名: gacha_history
パーティションキー: user_id (文字列)
ソートキー: timestamp (数値)
デフォルト設定を使用
キャパシティモード: オンデマンド
「テーブルを作成」をクリック

# server_settingsテーブル
テーブル名: server_settings
パーティションキー: server_id (文字列)
デフォルト設定を使用
キャパシティモード: オンデマンド
「テーブルを作成」をクリック
```

## 2. プロジェクトのセットアップ

```bash
# 2.1 プロジェクトディレクトリの作成と移動
mkdir discord-gacha-bot
cd discord-gacha-bot

# 2.2 必要なパッケージのインストール
pip install discord.py python-dotenv boto3
```

```bash
# 2.3 ディレクトリ構造の作成
mkdir cogs utils
```

```bash
# 2.4 .envファイルの作成
# .envファイルを作成し以下を記述
DISCORD_BOT_TOKEN=あなたのDiscordボットトークン
AWS_ACCESS_KEY_ID=あなたのAWSアクセスキーID
AWS_SECRET_ACCESS_KEY=あなたのAWSシークレットアクセスキー
```

## 3. コードファイルの作成

```python
# 3.1 utils/aws_database.py
import boto3
from datetime import datetime
import os

class AWSDatabase:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('discord_users')
        self.history_table = self.dynamodb.Table('gacha_history')
        self.settings_table = self.dynamodb.Table('server_settings')

    def get_user_data(self, user_id, server_id):
        response = self.users_table.get_item(
            Key={
                'user_id': f"{server_id}:{user_id}"
            }
        )
        return response.get('Item')

    def update_user_points(self, user_id, server_id, points, last_gacha_date):
        self.users_table.put_item(
            Item={
                'user_id': f"{server_id}:{user_id}",
                'points': points,
                'last_gacha_date': last_gacha_date,
                'updated_at': datetime.now().isoformat()
            }
        )

    def get_server_settings(self, server_id):
        response = self.settings_table.get_item(
            Key={
                'server_id': server_id
            }
        )
        return response.get('Item')

    def update_server_settings(self, server_id, settings):
        self.settings_table.put_item(
            Item={
                'server_id': server_id,
                'settings': settings,
                'updated_at': datetime.now().isoformat()
            }
        )

    def record_gacha_history(self, user_id, server_id, result_item, points):
        self.history_table.put_item(
            Item={
                'user_id': f"{server_id}:{user_id}",
                'timestamp': int(datetime.now().timestamp()),
                'item_name': result_item['name'],
                'points': points,
                'created_at': datetime.now().isoformat()
            }
        )
```

```python
# 3.2 main.py
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
```

## 4. ボットの実行

```bash
# 4.1 ボットの起動
python main.py

# 4.2 正常起動の確認
# 以下のようなメッセージが表示されることを確認
# BotName has connected to Discord!
# Bot is ready in X servers.
```

## 5. 動作確認

```
# 5.1 基本コマンドの確認
Discordサーバーで以下のコマンドを実行：
!gacha_setup (管理者のみ)
!gacha_panel (管理者のみ)

# 5.2 ガチャの実行
表示されたパネルのボタンをクリックしてガチャを実行

# 5.3 データベースの確認
AWSコンソールのDynamoDBで各テーブルを確認：
- discord_users: ユーザーデータが保存されているか
- gacha_history: ガチャ履歴が記録されているか
- server_settings: サーバー設定が保存されているか
```