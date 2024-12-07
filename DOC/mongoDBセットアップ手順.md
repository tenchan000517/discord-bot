では、MongoDBを使用したDiscordボットの環境構築の手順を説明します：

1. **EC2の基本設定**
```bash
# システムアップデート
sudo yum update -y

# Gitのインストール
sudo yum install -y git

# Node.jsのインストール（必要な場合）
curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs
```

2. **MongoDBのインストール**
```bash
# MongoDBリポジトリの設定
echo '[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc' | sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo

# MongoDBのインストール
sudo yum install -y mongodb-org

# MongoDBの起動と自動起動設定
sudo systemctl start mongod
sudo systemctl enable mongod

# ステータス確認
sudo systemctl status mongod
```

3. **Pythonの設定**
```bash
# Python 3とpip3のインストール
sudo yum install -y python3 python3-pip

# 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
pip install discord.py pymongo python-dotenv
```

4. **アプリケーションのセットアップ**
```bash
# アプリケーションディレクトリの作成
mkdir -p ~/discord-bot
cd ~/discord-bot

# GitHubからコードをクローン（もしリポジトリがある場合）
git clone your-repository-url .

# 環境変数の設定
cat > .env << EOF
DISCORD_BOT_TOKEN=your_discord_token
MONGODB_URI=mongodb://localhost:27017/discord_bot
EOF
```

5. **プロセス管理のセットアップ（PM2使用）**
```bash
# PM2のインストール
sudo npm install -g pm2

# 起動スクリプトの作成
cat > ecosystem.config.js << EOF
module.exports = {
  apps : [{
    name: 'discord-bot',
    script: 'main.py',
    interpreter: './venv/bin/python3',
    watch: true,
    env: {
      NODE_ENV: 'production'
    }
  }]
}
EOF

# ボットの起動
pm2 start ecosystem.config.js

# PM2の自動起動設定
pm2 startup
pm2 save
```

6. **バックアップスクリプトの設定**
```bash
# バックアップディレクトリの作成
sudo mkdir -p /opt/backups/mongodb
sudo chown -R ec2-user:ec2-user /opt/backups

# バックアップスクリプトの作成
cat > backup-mongodb.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/mongodb"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
mongodump --out \$BACKUP_DIR/\$TIMESTAMP
find \$BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +
EOF

# スクリプトの権限設定
chmod +x backup-mongodb.sh

# cronに追加（毎日午前3時に実行）
(crontab -l 2>/dev/null; echo "0 3 * * * $HOME/backup-mongodb.sh") | crontab -
```

7. **セキュリティ設定**
```bash
# MongoDBのセキュリティ設定
sudo vi /etc/mongod.conf

# 以下の設定を変更
# bindIp: 127.0.0.1  # ローカルアクセスのみ
# security:
#   authorization: enabled
```

8. **動作確認**
```bash
# MongoDBの接続確認
mongosh

# ボットの動作確認
pm2 logs discord-bot
```

9. **監視の設定**
```bash
# CloudWatchエージェントのインストール
sudo yum install -y amazon-cloudwatch-agent

# 設定ファイルの作成
sudo mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
sudo vi /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# エージェントの起動
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s
sudo systemctl start amazon-cloudwatch-agent
```

# Discord Bot用 MongoDB セットアップ完全ガイド

## 1. MongoDBのインストールと初期設定

### 1.1 MongoDBのインストール
```bash
# MongoDBリポジトリの設定
sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo << EOF
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

# パッケージキャッシュのクリーンと更新
sudo yum clean all
sudo yum makecache

# MongoDBのインストール
sudo yum install -y mongodb-org

# mongoshクライアントのインストール
sudo yum install -y mongodb-mongosh
```

### 1.2 MongoDBサービスの起動
```bash
# MongoDBサービスの起動
sudo systemctl start mongod

# 起動状態の確認
sudo systemctl status mongod

# システム起動時に自動起動するように設定
sudo systemctl enable mongod
```

## 2. 管理者ユーザーの作成と認証設定

### 2.1 mongoshでの接続
```bash
mongosh
```

### 2.2 管理者ユーザーの作成
```javascript
// adminデータベースに切り替え
use admin

// 管理者ユーザーの作成
db.createUser({
    user: "adminUser",
    pwd: "tenchan1341",  // パスワードは適切に変更してください
    roles: [ 
        { role: "userAdminAnyDatabase", db: "admin" },
        "readWriteAnyDatabase"
    ]
})
```

### 2.3 認証接続の確認
```bash
# 一旦mongoshを終了
exit

# 認証付きで再接続
mongosh --authenticationDatabase "admin" -u "adminUser" -p "tenchan1341"
```

## 3. Discordボット用データベースとコレクションの作成

### 3.1 データベースの作成と切り替え
```javascript
// Discord bot用データベースに切り替え
use discord_bot

// テストデータの挿入（データベース作成の確認用）
db.test.insertOne({ name: "test", value: 1 })

// データベース一覧の確認
show dbs
```

### 3.2 必要なコレクションの作成
```javascript
// コレクションの作成
db.createCollection("server_settings")
db.createCollection("users")
db.createCollection("gacha_history")

// コレクション一覧の確認
show collections
```

### 3.3 インデックスの作成
```javascript
// サーバー設定用インデックス
db.server_settings.createIndex({ "server_id": 1 }, { unique: true })

// ユーザーデータ用インデックス
db.users.createIndex({ "user_id": 1, "server_id": 1 }, { unique: true })

// ガチャ履歴用インデックス
db.gacha_history.createIndex({ "user_id": 1, "timestamp": -1 })

// インデックスの確認
db.server_settings.getIndexes()
db.users.getIndexes()
db.gacha_history.getIndexes()
```

### 3.4 サンプルデータの挿入
```javascript
// サーバー設定のサンプルデータ
db.server_settings.insertOne({
    server_id: "your_server_id",  // Discordサーバーのidを入力
    settings: {
        items: [
            {
                name: 'SSRアイテム',
                weight: 5,
                points: 100,
                image_url: ''
            },
            {
                name: 'SRアイテム',
                weight: 15,
                points: 50,
                image_url: ''
            },
            {
                name: 'Rアイテム',
                weight: 30,
                points: 30,
                image_url: ''
            },
            {
                name: 'Nアイテム',
                weight: 50,
                points: 10,
                image_url: ''
            }
        ]
    },
    updated_at: new Date()
})
```

## 4. バックアップ設定

### 4.1 バックアップディレクトリの作成
```bash
# mongoshを終了
exit

# バックアップディレクトリの作成
sudo mkdir -p /backup/mongodb

# 権限の設定
sudo chown -R ec2-user:ec2-user /backup/mongodb
```

### 4.2 バックアップの実行
```bash
# バックアップの作成
mongodump --uri="mongodb://adminUser:tenchan1341@localhost:27017/discord_bot?authSource=admin" --out=/backup/mongodb/$(date +%Y%m%d)
```

## 5. 接続文字列の設定

### 5.1 環境変数の設定
プロジェクトの`.env`ファイルに以下を追加：
```
MONGODB_URI=mongodb://adminUser:tenchan1341@localhost:27017/discord_bot?authSource=admin
```

## 6. 動作確認

### 6.1 データの確認
```javascript
// mongoshで再接続
mongosh --authenticationDatabase "admin" -u "adminUser" -p "tenchan1341"

// データベースの確認
use discord_bot

// 各コレクションの確認
db.server_settings.find()
db.users.find()
db.gacha_history.find()
```

## 重要な注意点
1. パスワードは必ず強固なものに変更してください
2. 本番環境では適切なファイアウォール設定を行ってください
3. 定期的なバックアップを設定することを推奨します
4. 実際のサーバーIDを使用する際は、正しいIDに置き換えてください

## トラブルシューティング
- MongoDBサービスが起動しない場合: `sudo systemctl status mongod` でログを確認
- 認証エラーが発生する場合: ユーザー名とパスワードを確認
- バックアップが失敗する場合: ディレクトリの権限を確認