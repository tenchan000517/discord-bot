# Discord Bot 更新・拡張ガイド

## 前提条件
- Visual Studio Code がインストールされていること
- Git がインストールされていること
- SSH クライアントがインストールされていること
- AWS アクセスキーとシークレットキーが用意されていること
- Discord Bot トークンが用意されていること

## 1. Discord Bot のアップデート手順

### ローカルでの開発
1. VS Code でプロジェクトを開く
```bash
code discord-gacha-bot
```

<!-- 2. 必要な変更を加える
   - `cogs/gacha.py`
   - `utils/aws_database.py`
   - `main.py`
   などの必要なファイルを編集 -->

3. ローカルでテスト
```bash
python main.py
```

### EC2へのデプロイ
# Discord Bot 実践的アップデートガイド

## 1. EC2サーバーへの接続

1. VS Codeでプロジェクトフォルダを開く
```bash
cd /c/discord-gacha-bot
```

2. EC2への接続
```bash
ssh -i "C:/discord-gacha-bot/discord-bot-key.pem" ec2-user@18.181.82.180
```

## 2. Botの停止とコード更新

接続できたら、以下のコマンドを順番に実行：

1. 現在動いているBotを停止
```bash
sudo systemctl stop discord-bot
```

2. プロジェクトディレクトリに移動してコードを更新
```bash
cd ~/discord-bot
git pull origin main
```

3. 仮想環境を有効化して依存関係を更新（新しいパッケージを追加した場合のみ）
```bash
source venv/bin/activate
pip install -r requirements.txt
```

4. Botを再起動
```bash
sudo systemctl start discord-bot
```

## 3. 動作確認

1. ログの確認
```bash
# 通常のログを確認
tail -f /var/log/discord-bot/discord.log

# エラーログの確認（必要な場合）
tail -f /var/log/discord-bot/discord.error.log
```

2. Botのステータス確認
```bash
sudo systemctl status discord-bot
```

## トラブルシューティング

問題が発生した場合の対処方法：

1. エラーの詳細確認
```bash
journalctl -u discord-bot
```

2. サービスの再起動
```bash
sudo systemctl restart discord-bot
```

3. プロセスの確認
```bash
ps aux | grep discord-bot
```

## 注意点
- EC2接続時は必ず正しいpemファイルとIPアドレスを使用する
- Botの停止→更新→起動の順序を必ず守る
- 更新後は必ずログを確認する
- 問題が発生した場合はエラーログを確認する

## 補足：ローカルでの開発（更新する内容がある場合）

1. VS Codeでファイルを編集

2. 変更をGitに反映
```bash
git add .
git commit -m "更新内容の説明"
git push origin main
```

その後、上記の「1. EC2サーバーへの接続」から実行

## 2. データベース拡張手順

### 新しいテーブルの追加
1. `utils/aws_database.py` に新しいテーブル定義を追加
```python
def __init__(self):
    self.dynamodb = boto3.resource('dynamodb')
    self.users_table = self.dynamodb.Table('discord_users')
    self.settings_table = self.dynamodb.Table('server_settings')
    self.history_table = self.dynamodb.Table('gacha_history')
    self.new_table = self.dynamodb.Table('new_table_name')  # 新しいテーブル
```

2. AWS Management Console でテーブルを作成
   - DynamoDB コンソールにアクセス
   - 「テーブルの作成」をクリック
   - テーブル名、パーティションキー、ソートキー（必要な場合）を設定
   - 必要なインデックスを設定
   - キャパシティモードを選択（オンデマンドまたはプロビジョンド）

3. 新しいメソッドの追加
```python
def new_table_operation(self, parameters):
    try:
        response = self.new_table.put_item(
            Item={
                'pk': 'some_key',
                'data': 'some_data'
            }
        )
        return True
    except Exception as e:
        print(f"Error in new operation: {e}")
        return False
```

### 既存テーブルの修正
1. バックアップの作成
   - AWS Management Console でテーブルを選択
   - 「バックアップ」タブ
   - 「バックアップの作成」をクリック

2. テーブル構造の変更
   - 新しい GSI（Global Secondary Index）の追加
   - 属性の追加（DynamoDB は柔軟なスキーマ）

## 3. 新しいDiscordサーバーの追加手順

### サーバー追加の準備
1. Discord Developer Portal で Bot の設定確認
   - 必要な権限が付与されていることを確認
   - OAuth2 URL の生成

2. データベース設計の確認
   - 現在の実装は既にサーバーごとの分離に対応済み
   - PKの形式: `USER#{user_id}#SERVER#{server_id}`
   - 追加の設定は不要

### 新しいサーバーへのBot追加
1. OAuth2 URL を使用してBotを招待
   - 生成したURLをブラウザで開く
   - サーバーを選択
   - 必要な権限を確認して「認証」をクリック

2. サーバー初期設定
```bash
# Discordサーバー内で実行
!gacha_setup
```

3. 動作確認
   - ガチャパネルが正しく表示されることを確認
   - ポイントシステムのテスト
   - ロール付与の確認

## トラブルシューティング

### ログの確認
```bash
# 通常ログ
tail -f /var/log/discord-bot/discord.log

# エラーログ
tail -f /var/log/discord-bot/discord.error.log

# システムログ
journalctl -u discord-bot
```

### よくある問題と解決方法
1. Bot が応答しない
   - サービスの状態確認: `sudo systemctl status discord-bot`
   - トークンの確認: `.env` ファイルの内容を確認
   - ネットワーク接続の確認

2. データベースエラー
   - AWS認証情報の確認
   - DynamoDBテーブルの状態確認
   - IAMポリシーの確認

3. 権限エラー
   - Botの権限設定の確認
   - サーバー内でのロール階層の確認

## セキュリティ注意事項
- `.env` ファイルを Git にコミットしない
- AWS認証情報を安全に管理する
- バックアップを定期的に作成する
- ログに機密情報が含まれていないか確認する