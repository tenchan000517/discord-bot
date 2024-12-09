# settings/modals/gacha_items.py
import discord
from .base import BaseSettingsModal
import json

class GachaItemsModal(BaseSettingsModal):
    def __init__(self, settings, settings_manager):
        super().__init__(title="ガチャアイテム設定", settings=settings)
        self.settings_manager = settings_manager

        # 既存のアイテムをJSONとして整形
        existing_items = settings.items or []
        items_json = json.dumps(existing_items, ensure_ascii=False, indent=2) if existing_items else """[
  {
    "name": "レアアイテム",
    "weight": "10",
    "points": "1000",
    "image_url": "https://example.com/rare.png"
  },
  {
    "name": "ノーマルアイテム",
    "weight": "90",
    "points": "100",
    "image_url": "https://example.com/normal.png"
  }
]"""

        self.items_input = discord.ui.TextInput(
            label="アイテム設定（JSON形式）",
            style=discord.TextStyle.paragraph,
            placeholder="JSONフォーマットでアイテムを設定してください",
            default=items_json,
            required=True,
            max_length=4000
        )
        self.add_item(self.items_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # JSONの解析
            items = json.loads(self.items_input.value)
            
            # バリデーション
            if not isinstance(items, list):
                raise ValueError("アイテムはリスト形式で指定してください")

            for item in items:
                if not all(key in item for key in ['name', 'weight', 'points']):
                    raise ValueError("各アイテムには name, weight, points が必要です")
                
                # 数値の検証
                try:
                    float(item['weight'])
                    int(float(item['points']))
                except ValueError:
                    raise ValueError("weight と points は数値である必要があります")

                # URLの検証（存在する場合）
                if 'image_url' in item and item['image_url']:
                    valid_url, error_msg = await self._validate_url(item['image_url'])
                    if not valid_url:
                        raise ValueError(f"URLエラー: {error_msg}")

            # 更新する設定を生成
            updated_settings = {
                'enabled': self.settings.enabled,
                'messages': self.settings.messages.to_dict() if self.settings.messages else None,
                'media': self.settings.media.to_dict() if self.settings.media else None,
                'items': items
            }

            # 設定を保存
            success = await self.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'gacha',
                updated_settings
            )
            
            if success:
                await interaction.response.send_message(
                    f"✅ {len(items)}個のアイテムを設定しました。\n\n" + \
                    "\n".join([f"・{item['name']} (確率: {item['weight']}%, {item['points']}ポイント)" 
                              for item in items[:5]]) + \
                    ("\n..." if len(items) > 5 else ""),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ 設定の更新に失敗しました。",
                    ephemeral=True
                )

        except json.JSONDecodeError:
            await interaction.response.send_message(
                "❌ 無効なJSON形式です。\n入力内容を確認してください。",
                ephemeral=True
            )
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ 設定エラー: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error updating gacha items: {e}")
            await interaction.response.send_message(
                "❌ エラーが発生しました。\n入力内容を確認してください。",
                ephemeral=True
            )

    async def _update_feature_settings(self, interaction: discord.Interaction, feature: str, updated_settings: dict) -> bool:
        """機能の設定をDynamoDBに保存"""
        try:
            server_id = str(interaction.guild_id)
            print(f"[INFO] Updating {feature} settings for server_id: {server_id}")
            print(f"[DEBUG] Updated settings: {updated_settings}")

            success = await self.settings_manager.update_feature_settings(server_id, feature, updated_settings)
            
            if not success:
                print(f"[ERROR] Failed to update {feature} settings in the database")
                return False

            return True
        except Exception as e:
            print(f"[ERROR] Failed to update {feature} settings: {e}")
            return False