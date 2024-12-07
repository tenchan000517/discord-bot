# AWS環境構築ガイド - Discordボット用インフラ

## 1. AWSアカウントのセットアップ

### 1.1 IAMユーザーの作成
1. AWSマネジメントコンソールにログイン
2. IAMダッシュボードに移動
3. 以下の権限を持つIAMユーザーを作成:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:*",
                "lambda:*",
                "cloudwatch:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### 1.2 アクセスキーの設定
1. IAMユーザーの「セキュリティ認証情報」タブを開く
2. アクセスキーを作成
3. アクセスキーとシークレットキーを安全に保管

## 2. DynamoDBのセットアップ

### 2.1 テーブルの作成
1. DynamoDBコンソールに移動
2. 「テーブルの作成」をクリック
3. ユーザーテーブルの設定:
```yaml
テーブル名: discord_users
パーティションキー: user_id (String)
ソートキー: なし
キャパシティモード: プロビジョンド
読み取り容量ユニット: 5
書き込み容量ユニット: 5
```

4. ガチャ履歴テーブルの設定:
```yaml
テーブル名: gacha_history
パーティションキー: user_id (String)
ソートキー: timestamp (Number)
キャパシティモード: プロビジョンド
読み取り容量ユニット: 5
書き込み容量ユニット: 5
```

### 2.2 Auto Scalingの設定
```yaml
MinCapacity: 5
MaxCapacity: 20
TargetValue: 70
ScaleInCooldown: 60
ScaleOutCooldown: 60
```

## 3. Lambda関数の作成

### 3.1 基本設定
1. Lambda コンソールに移動
2. 「関数の作成」をクリック
3. 以下の設定で関数を作成:
```yaml
関数名: discord-bot-handler
ランタイム: Node.js 18.x
アーキテクチャ: x86_64
メモリ: 128 MB
タイムアウト: 30秒
```

### 3.2 環境変数の設定
```yaml
DISCORD_TOKEN: "your-bot-token"
DYNAMODB_USERS_TABLE: "discord_users"
DYNAMODB_HISTORY_TABLE: "gacha_history"
AWS_REGION: "ap-northeast-1"
```

### 3.3 基本的なハンドラーコード
```javascript
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
    try {
        // Discordからのイベント処理
        const { type, data } = JSON.parse(event.body);
        
        // ユーザーデータの取得
        const userData = await dynamodb.get({
            TableName: process.env.DYNAMODB_USERS_TABLE,
            Key: {
                user_id: data.user_id
            }
        }).promise();
        
        // イベントに応じた処理
        switch (type) {
            case 'GACHA':
                return handleGacha(userData.Item, data);
            case 'PROFILE':
                return handleProfile(userData.Item);
            default:
                return {
                    statusCode: 400,
                    body: JSON.stringify({ error: 'Unknown event type' })
                };
        }
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Internal server error' })
        };
    }
};
```

## 4. CloudWatchの設定

### 4.1 メトリクスの設定
1. CloudWatchコンソールに移動
2. 以下のメトリクスを設定:
```yaml
- DynamoDB:
    - ConsumedReadCapacityUnits
    - ConsumedWriteCapacityUnits
    - ThrottledRequests
- Lambda:
    - Invocations
    - Errors
    - Duration
```

### 4.2 アラートの設定
```yaml
アラート条件:
  - エラー率が1%を超えた場合
  - Lambda実行時間が5秒を超えた場合
  - DynamoDBのスロットリングが発生した場合
通知方法:
  - Amazon SNS経由でメール通知
```

## 5. バックアップとリカバリー

### 5.1 自動バックアップの設定
```yaml
DynamoDBテーブル:
  BackupConfig:
    PointInTimeRecovery: Enabled
    BackupRetentionPeriod: 35 # 日数
```

### 5.2 定期的なフルバックアップ
AWS Backupを使用して週次フルバックアップを設定:
```yaml
バックアップルール:
  スケジュール: 毎週日曜日 AM 2:00
  保持期間: 90日
  コピー先リージョン: ap-northeast-2
```

## 6. セキュリティ設定

### 6.1 暗号化の設定
```yaml
DynamoDBテーブル:
  SSE:
    Enabled: true
    KMSMasterKeyId: aws/dynamodb

Lambda環境変数:
  暗号化: AWS KMS
```

### 6.2 ネットワーク設定
```yaml
Lambda関数:
  VPC設定: 必要に応じて
  セキュリティグループ:
    - インバウンド: 必要最小限
    - アウトバウンド: 必要なAWSサービスのみ
```

## 7. デプロイメント手順

### 7.1 初期デプロイ
```bash
# AWS CLIの設定
aws configure

# DynamoDBテーブルの作成
aws dynamodb create-table --cli-input-json file://table-definition.json

# Lambda関数のデプロイ
zip -r function.zip .
aws lambda create-function --function-name discord-bot-handler \
    --runtime nodejs18.x \
    --handler index.handler \
    --zip-file fileb://function.zip \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-role
```

### 7.2 更新手順
```bash
# コードの更新
zip -r function.zip .
aws lambda update-function-code \
    --function-name discord-bot-handler \
    --zip-file fileb://function.zip
```

## 8. モニタリングとメンテナンス

### 8.1 定期チェック項目
- DynamoDBの使用率とコスト
- Lambda関数のエラー率
- API レスポンスタイム
- バックアップの成功率

### 8.2 最適化のためのチェックポイント
- 毎月1回:
  - コストレビュー
  - パフォーマンス分析
  - キャパシティ調整
- 四半期ごと:
  - セキュリティ設定の見直し
  - バックアップ戦略の評価
  - スケーリング設定の最適化

  # 修正版ロードマップ - Discordガチャボット

## EC2選択の理由
1. **コスト効率**
   - t2.micro（無料枠対象）で開始可能
   - 予測可能な固定費用（$5-10/月）
   - Lambdaの場合、24時間常時接続で予期せぬ高額請求の可能性

2. **技術的適合性**
   - Discordボットの常時接続要件に最適
   - 現行コードの移行が容易
   - WebSocket接続の維持が自然に行える

3. **運用の容易さ**
   - シンプルなアーキテクチャ
   - 直接的なログアクセス
   - 柔軟なモニタリング設定

## 1. 初期フェーズ（0-1000ユーザー）
【✓完了】データベース構築
- DynamoDBテーブル作成
  - discord_users
  - gacha_history
  - server_settings
- 基本的なCRUD操作の実装

【現在ここ】24時間稼働環境の構築
1. EC2インスタンスのセットアップ
   - t2.microインスタンスの作成
   - セキュリティグループの設定
   - SSHアクセスの設定
2. デプロイ環境の整備
   - Git連携
   - 自動デプロイの検討
3. モニタリングの設定
   - CloudWatchによる基本メトリクス監視
   - アラート設定

コスト見積もり:
- EC2 (t2.micro): $0-5/月（無料枠利用可）
- DynamoDB: $2-3/月
- CloudWatch: $0-2/月
総コスト: 月額$2-10

## 2. 成長フェーズ（1000-5000ユーザー）
1. パフォーマンス最適化
   - DynamoDBのオートスケーリング設定
   - EC2インスタンスのリソース監視と必要に応じたスケールアップ
2. バックアップ戦略
   - 定期的なAMIバックアップ
   - DynamoDBバックアップ設定
3. 監視の強化
   - 詳細なメトリクス収集
   - カスタムダッシュボードの作成

コスト見積もり:
- EC2 (t2.small/medium): $10-20/月
- DynamoDB: $5-10/月
- バックアップ・監視: $5-10/月
総コスト: 月額$20-40

## 3. 拡大フェーズ（5000-20000ユーザー）
1. インフラ強化
   - 必要に応じたEC2スケールアップ
   - リージョン冗長化の検討
2. パフォーマンスチューニング
   - DynamoDBインデックス最適化
   - キャッシュ層の検討
3. 運用の自動化
   - デプロイ自動化の完備
   - 障害復旧プロセスの確立

コスト見積もり:
- EC2 (t2.medium/large): $20-40/月
- DynamoDB: $15-30/月
- 運用管理: $10-20/月
総コスト: 月額$45-90

## 4. 大規模フェーズ（20000+ユーザー）
1. 高可用性対応
   - マルチAZ展開
   - ロードバランサーの導入
2. データ管理の高度化
   - 読み取り/書き込みの分離
   - アナリティクス基盤の追加
3. 運用の高度化
   - 詳細なモニタリング
   - 自動スケーリングの完備

コスト見積もり:
- インフラ全体: $100-200/月
- 運用管理: $50-100/月
総コスト: 月額$150-300