# Discord Bot DynamoDB移行手順書

## 1. 環境準備

### 1.1 必要なパッケージのインストール
```bash
# AWS関連パッケージのインストール
pip uninstall awscli boto3 botocore s3transfer -y
pip install boto3
```

### 1.2 環境変数の設定
```env
# .envファイルに以下を設定
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-northeast-1
DISCORD_BOT_TOKEN=your_discord_token
```

## 2. データベース構築

### 2.1 テーブル作成スクリプトの準備
```python
# create_tables.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_dynamodb_tables():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # discord_usersテーブル
        users_table = dynamodb.create_table(
            TableName='discord_users',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'last_gacha_date', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'last_gacha_date', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # server_settingsテーブル
        settings_table = dynamodb.create_table(
            TableName='server_settings',
            KeySchema=[
                {'AttributeName': 'server_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'server_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # gacha_historyテーブル
        history_table = dynamodb.create_table(
            TableName='gacha_history',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        print("テーブル作成中...")
        users_table.meta.client.get_waiter('table_exists').wait(TableName='discord_users')
        settings_table.meta.client.get_waiter('table_exists').wait(TableName='server_settings')
        history_table.meta.client.get_waiter('table_exists').wait(TableName='gacha_history')
        print("テーブルの作成が完了しました！")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    create_dynamodb_tables()
```

### 2.2 テーブル確認スクリプトの準備
```python
# check_tables.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def list_tables():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        tables = list(dynamodb.tables.all())
        print("作成されたテーブル:")
        for table in tables:
            print(f"- {table.name}")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    list_tables()
```

### 2.3 データベース操作クラスの準備
```python
# utils/aws_database.py
import boto3
from datetime import datetime
import os
import pytz

class AWSDatabase:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        self.history_table = self.dynamodb.Table('gacha_history')

    def get_user_data(self, user_id, server_id):
        try:
            response = self.users_table.get_item(
                Key={
                    'user_id': f"{server_id}:{user_id}",
                    'last_gacha_date': 'CURRENT'
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None

    def update_user_points(self, user_id, server_id, points, last_gacha_date):
        try:
            self.users_table.put_item(
                Item={
                    'user_id': f"{server_id}:{user_id}",
                    'last_gacha_date': last_gacha_date,
                    'points': points,
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating user points: {e}")
            return False

    def record_gacha_history(self, user_id, server_id, result_item, points):
        try:
            self.history_table.put_item(
                Item={
                    'user_id': f"{server_id}:{user_id}",
                    'timestamp': int(datetime.now().timestamp()),
                    'item_name': result_item['name'],
                    'points': points,
                    'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error recording gacha history: {e}")
            return False
```

## 3. 実行手順

1. 必要なファイルの配置を確認
```
├── .env                  # 環境変数ファイル
├── create_tables.py      # テーブル作成スクリプト
├── check_tables.py       # テーブル確認スクリプト
├── main.py              # Botメインファイル
└── utils/
    └── aws_database.py  # データベース操作クラス
```

2. テーブルの作成
```bash
python create_tables.py
```

3. テーブルの確認
```bash
python check_tables.py
```

4. Botの起動
```bash
python main.py
```

## 4. エラー対応

エラーが発生した場合の一般的な確認事項：
1. .envファイルの内容が正しいか確認
2. AWS認証情報が有効か確認
3. リージョンが正しく設定されているか確認
4. 必要なパッケージがすべてインストールされているか確認