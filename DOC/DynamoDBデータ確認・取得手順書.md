# DynamoDB データ確認・取得手順書

## 1. データベース内容の確認

### EC2サーバーでの確認

# データベース確認の具体的手順

## 1. EC2への接続（ローカルのVS Codeターミナルで実行）
```bash
# プロジェクトディレクトリに移動
cd /c/discord-gacha-bot

# EC2に接続
ssh -i "C:/discord-gacha-bot/discord-bot-key.pem" ec2-user@18.181.82.180
```

## 2. データ確認準備（EC2サーバー側のターミナルで実行）
```bash
# Botのディレクトリに移動
cd ~/discord-bot

# 仮想環境を有効化
source venv/bin/activate

# Pythonインタラクティブシェルを起動
python
```

## 3. データ確認（Pythonインタラクティブシェル内で実行）
```python
# 必要なモジュールをインポート
import boto3
from utils.aws_database import AWSDatabase

# データベース接続
db = AWSDatabase()

# テーブルごとのデータ確認
# ユーザーデータの確認
response = db.users_table.scan()
print("Users:", response['Items'])

# サーバー設定の確認
response = db.settings_table.scan()
print("Settings:", response['Items'])

# ガチャ履歴の確認
response = db.history_table.scan()
print("History:", response['Items'])
```

## 4. 終了方法
```python
# Pythonシェルを終了する場合
exit()

# 仮想環境を終了する場合（EC2サーバー側のターミナルで）
deactivate

# EC2との接続を切る場合
exit
```

1. VS Codeを開き、ターミナルで接続
```bash
cd /c/discord-gacha-bot
ssh -i "C:/discord-gacha-bot/discord-bot-key.pem" ec2-user@18.181.82.180
```

2. Pythonインタラクティブシェルを使用してデータ確認
```bash
# 仮想環境の有効化
cd ~/discord-bot
source venv/bin/activate

# Pythonシェルを起動
python

# 以下はPythonシェル内で実行
import boto3
from utils.aws_database import AWSDatabase

# データベース接続
db = AWSDatabase()

# テーブルごとのデータ確認
# ユーザーデータの確認
response = db.users_table.scan()
print("Users:", response['Items'])

# サーバー設定の確認
response = db.settings_table.scan()
print("Settings:", response['Items'])

# ガチャ履歴の確認
response = db.history_table.scan()
print("History:", response['Items'])
```

### AWS Management Consoleでの確認

1. AWSコンソールにログイン

2. DynamoDBサービスに移動
   - サービス検索で「DynamoDB」を選択
   - リージョンが「アジアパシフィック（東京）ap-northeast-1」であることを確認

3. テーブル一覧の確認
   - `discord_users`
   - `server_settings`
   - `gacha_history`

4. 各テーブルのデータ確認
   - テーブル名をクリック
   - 「項目を探索」タブを選択
   - データを確認

## 2. データ取得ロジックの実装

### 新しい取得メソッドの追加

1. VS CodeでAWSデータベースクラスを開く
```bash
code /c/discord-gacha-bot/utils/aws_database.py
```

2. 新しいメソッドの実装例

```python
# 特定ユーザーの全サーバーデータ取得
def get_user_all_servers(self, user_id):
    try:
        response = self.users_table.query(
            IndexName='UserIndex',  # セカンダリインデックスを使用
            KeyConditionExpression=Key('user_id').eq(str(user_id))
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting user's server data: {e}")
        return []

# サーバー内の上位ユーザー取得
def get_top_users(self, server_id, limit=10):
    try:
        response = self.users_table.query(
            IndexName='ServerIndex',  # セカンダリインデックスを使用
            KeyConditionExpression=Key('server_id').eq(str(server_id)),
            Limit=limit,
            ScanIndexForward=False  # 降順でソート
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting top users: {e}")
        return []

# 期間指定でのガチャ履歴取得
def get_gacha_history_by_period(self, start_date, end_date):
    try:
        response = self.history_table.scan(
            FilterExpression=
                Attr('created_at').between(start_date, end_date)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting gacha history: {e}")
        return []
```

3. 変更をGitに反映
```bash
git add utils/aws_database.py
git commit -m "Add new database query methods"
git push origin main
```

4. EC2に接続して更新を反映
```bash
ssh -i "C:/discord-gacha-bot/discord-bot-key.pem" ec2-user@18.181.82.180
cd ~/discord-bot
git pull origin main
sudo systemctl restart discord-bot
```

## 3. データ取得の動作確認

### EC2上での確認

```python
# Pythonシェルを起動して確認
python

# テストコード
from utils.aws_database import AWSDatabase
db = AWSDatabase()

# 新しいメソッドのテスト
test_user_id = "123456789"  # テスト対象のユーザーID
test_server_id = "987654321"  # テスト対象のサーバーID

# ユーザーの全サーバーデータを取得
user_servers = db.get_user_all_servers(test_user_id)
print("User's servers:", user_servers)

# サーバーの上位ユーザーを取得
top_users = db.get_top_users(test_server_id)
print("Top users:", top_users)
```

## 注意点とベストプラクティス

1. データベースアクセス
   - 大量のデータを取得する場合はページネーションを使用
   - フィルタリングはなるべくインデックスを使用
   - スキャン操作は避け、クエリを使用

2. エラーハンドリング
   - 全てのデータベース操作でtry-exceptを使用
   - エラーは適切にログに記録

3. セキュリティ
   - 認証情報は必ず環境変数で管理
   - 本番環境のデータは慎重に扱う
   - テスト時は小さなデータセットで確認