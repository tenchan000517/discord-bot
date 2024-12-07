# 実装計画

## 1. 既存テーブルの拡張
- discord_users テーブルに新規フィールドを追加
  - ウォレット情報
  - 戦績情報
  - 実績情報
- server_settings テーブルに新規設定を追加
  - ランブル設定
  - ウォレット設定

  # 1. 既存テーブルの拡張方法

## discord_users テーブルの拡張
{
    'pk': 'USER#1234#SERVER#5678',
    'user_id': '1234',
    'server_id': '5678',
    'points': 100,
    'last_gacha_date': '2024-12-06',
    // 新規追加フィールド
    'wallet_address': 'eth_address_here',  // ウォレット情報
    'stats': {  // 戦績情報
        'rumble': {
            'wins': 10,
            'losses': 5,
            'points': 150
        }
    },
    'achievements': {  // 実績情報
        'gacha_legends': true,
        'rumble_master': false
    },
    'updated_at': '2024-12-06T...'
}

## server_settings テーブルの拡張
{
    'server_id': '5678',
    'settings': {
        'items': [...],  // 既存のガチャアイテム
        'rumble': {  // 新規追加設定
            'points_per_win': 50,
            'points_per_loss': 10,
            'cooldown_minutes': 30
        },
        'wallet': {  // ウォレット関連設定
            'required': false,
            'allowed_chains': ['ETH', 'SOL']
        }
    },
    'updated_at': '2024-12-06T...'
}

## gacha_history テーブルの拡張（既存）
{
    'pk': 'USER#1234#SERVER#5678',
    'timestamp': 1701234567,
    'user_id': '1234',
    'server_id': '5678',
    'item_name': 'SSRアイテム',
    'points': 100,
    'created_at': '2024-12-06T...'
}

# 2. 新規テーブル追加

## rumble_history テーブル作成
{
    'TableName': 'rumble_history',
    'KeySchema': [
        {
            'AttributeName': 'pk',  // USER#1234#SERVER#5678
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'timestamp',
            'KeyType': 'RANGE'
        }
    ],
    'AttributeDefinitions': [
        {
            'AttributeName': 'pk',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'timestamp',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'server_id',
            'AttributeType': 'S'
        }
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'ServerTimeIndex',
            'KeySchema': [
                {
                    'AttributeName': 'server_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            }
        }
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

## wallet_verification テーブル作成
{
    'TableName': 'wallet_verification',
    'KeySchema': [
        {
            'AttributeName': 'wallet_address',
            'KeyType': 'HASH'
        }
    ],
    'AttributeDefinitions': [
        {
            'AttributeName': 'wallet_address',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'user_id',
            'AttributeType': 'S'
        }
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'UserIndex',
            'KeySchema': [
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            }
        }
    ],
    'BillingMode': 'PAY_PER_REQUEST'
}

## 2. 新規テーブルの追加
- rumble_history テーブル
  - 対戦履歴の保存
  - ランキング集計用データ
- wallet_verification テーブル
  - ウォレット認証情報の管理
  - ユーザーとウォレットの紐付け

## 3. 実装手順

### Phase 1: 既存テーブルの拡張
```python
# aws_database.py に新規メソッドを追加

def update_user_wallet(self, user_id, server_id, wallet_address):
    try:
        pk = self._create_pk(user_id, server_id)
        response = self.users_table.update_item(
            Key={'pk': pk},
            UpdateExpression="SET wallet_address = :w, updated_at = :t",
            ExpressionAttributeValues={
                ':w': wallet_address,
                ':t': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating wallet: {e}")
        return False

def update_user_stats(self, user_id, server_id, game_type, stats_update):
    try:
        pk = self._create_pk(user_id, server_id)
        response = self.users_table.update_item(
            Key={'pk': pk},
            UpdateExpression="SET stats.#game = :s, updated_at = :t",
            ExpressionAttributeNames={
                '#game': game_type
            },
            ExpressionAttributeValues={
                ':s': stats_update,
                ':t': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating stats: {e}")
        return False
```

### Phase 2: 新規テーブル作成
```python
# create_new_tables.py
async def create_new_tables():
    try:
        # rumble_history テーブル作成
        await create_rumble_history_table()
        
        # wallet_verification テーブル作成
        await create_wallet_verification_table()
        
    except Exception as e:
        print(f"Error creating tables: {e}")

# 既存のテーブルは変更せず、新規テーブルのみ作成
```

### Phase 3: 新機能の実装

```python
# cogs/rumble.py
class Rumble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command()
    async def challenge(self, ctx, opponent: discord.Member):
        # ランブル機能の実装
        pass

# cogs/wallet.py
class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command()
    async def register_wallet(self, ctx, wallet_address: str):
        # ウォレット登録機能の実装
        pass
```

## 4. スケーリングのポイント

1. 非破壊的な更新
   - 既存のテーブルは構造を維持
   - 新規フィールドの追加のみ
   - 新機能は新規テーブルとして追加

2. 柔軟な拡張性
   - JSON型フィールドを活用
   - GSIを活用した検索性能の確保
   - マイグレーション不要な設計

3. 互換性の維持
   - 既存機能は変更なく動作継続
   - 新機能は既存機能と独立して追加可能
   - 段階的なデプロイが可能