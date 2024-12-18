import discord
from .base import BaseSettingsModal
from discord.ui import View
import json
from typing import Optional, List, Dict, Any

class GachaItemsView(View):
    def __init__(self, settings, settings_manager):
        super().__init__(timeout=None)
        self.settings = settings
        self.settings_manager = settings_manager
        self.existing_items = settings.items if settings.items is not None else []
        
        for i, item in enumerate(self.existing_items):
            button = discord.ui.Button(
                label=f"{item['name']} ({item['weight']}%, {item['points']}pts)",
                custom_id=f"edit_item_{i}",
                style=discord.ButtonStyle.secondary,
                row=i // 3  # 3つずつボタンを配置
            )
            button.callback = self.create_item_callback(i)
            self.add_item(button)

        # 追加ボタン
        add_button = discord.ui.Button(
            label="新規アイテム追加",
            style=discord.ButtonStyle.success,
            custom_id="add_item",
            row=(len(self.existing_items) // 3) + 1
        )
        add_button.callback = self.add_item_callback
        self.add_item(add_button)

        # 戻るボタン
        back_button = discord.ui.Button(
            label="戻る",
            style=discord.ButtonStyle.primary,
            custom_id="back_to_settings",
            row=(len(self.existing_items) // 3) + 1
        )
        back_button.callback = self.back_callback
        self.add_item(back_button)

    def create_item_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            modal = GachaItemsModal(
                settings=self.settings,
                settings_manager=self.settings_manager,
                item_index=index,
                existing_items=self.existing_items
            )
            await interaction.response.send_modal(modal)
        return callback

    async def add_item_callback(self, interaction: discord.Interaction):
        modal = GachaItemsModal(
            settings=self.settings,
            settings_manager=self.settings_manager,
            existing_items=self.existing_items
        )
        await interaction.response.send_modal(modal)

    async def back_callback(self, interaction: discord.Interaction):
        from .settings_view import SettingsView
        try:
            view = GachaSettingsView(interaction.client, self.settings)
            embed = await view.create_settings_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"Error returning to settings view: {e}")
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

class GachaItemsModal(BaseSettingsModal):
    def __init__(self, settings, settings_manager, item_index: Optional[int] = None, existing_items: Optional[List[Dict[str, Any]]] = None):
        # item_indexが指定されている場合は編集モード、Noneの場合は新規追加モード
        is_edit_mode = item_index is not None
        title = "ガチャアイテム編集" if is_edit_mode else "ガチャアイテム追加"
        super().__init__(title=title, settings=settings)
        
        self.settings_manager = settings_manager
        self.item_index = item_index
        self.existing_items = existing_items or []
        
        # 編集対象のアイテムを取得
        default_item = None
        if is_edit_mode and 0 <= item_index < len(self.existing_items):
            default_item = self.existing_items[item_index]

        # フィールドの追加
        self.name_input = discord.ui.TextInput(
            label="アイテム名",
            style=discord.TextStyle.short,
            placeholder="例：レアアイテム",
            default=default_item['name'] if default_item else "",
            required=True,
            max_length=100
        )
        self.add_item(self.name_input)

        self.weight_input = discord.ui.TextInput(
            label="出現確率（%）",
            style=discord.TextStyle.short,
            placeholder="例：10",
            default=str(default_item['weight']) if default_item else "",
            required=True,
            max_length=10
        )
        self.add_item(self.weight_input)

        self.points_input = discord.ui.TextInput(
            label="獲得ポイント",
            style=discord.TextStyle.short,
            placeholder="例：1000",
            default=str(default_item['points']) if default_item else "",
            required=True,
            max_length=10
        )
        self.add_item(self.points_input)

        self.image_url_input = discord.ui.TextInput(
            label="画像URL（省略可）",
            style=discord.TextStyle.short,
            placeholder="例：https://example.com/rare.png",
            default=default_item.get('image_url', "") if default_item else "",
            required=False,
            max_length=200
        )
        self.add_item(self.image_url_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # 入力値の検証
            try:
                weight = float(self.weight_input.value)
                points = int(float(self.points_input.value))
            except ValueError:
                raise ValueError("確率とポイントは数値である必要があります")

            # URLの検証（入力されている場合）
            if self.image_url_input.value:
                valid_url, error_msg = await self._validate_url(self.image_url_input.value)
                if not valid_url:
                    raise ValueError(f"URLエラー: {error_msg}")

            # 新しいアイテムの作成
            new_item = {
                'name': self.name_input.value,
                'weight': self.weight_input.value,
                'points': self.points_input.value,
                'image_url': self.image_url_input.value if self.image_url_input.value else None
            }

            # 既存のアイテムリストを更新
            updated_items = self.existing_items.copy()
            if self.item_index is not None:
                # 編集モード
                if 0 <= self.item_index < len(updated_items):
                    updated_items[self.item_index] = new_item
                    action = "編集"
            else:
                # 新規追加モード
                updated_items.append(new_item)
                action = "追加"

            # 更新する設定を生成
            updated_settings = {
                'enabled': self.settings.enabled,
                'messages': self.settings.messages.to_dict() if self.settings.messages else None,
                'media': self.settings.media.to_dict() if self.settings.media else None,
                'items': updated_items
            }

            # 設定を保存
            success = await self._update_feature_settings(
                interaction,
                'gacha',
                updated_settings
            )
            
            if success:
                # 削除用のViewを作成
                delete_view = None
                if self.item_index is not None:
                    class DeleteView(View):
                        def __init__(self):
                            super().__init__(timeout=None)
                            
                        @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
                        async def delete_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                            try:
                                updated_items.pop(self.item_index)
                                updated_settings['items'] = updated_items
                                success = await self._update_feature_settings(
                                    button_interaction,
                                    'gacha',
                                    updated_settings
                                )
                                if success:
                                    items_view = GachaItemsView(self.settings, self.settings_manager)
                                    await button_interaction.response.edit_message(
                                        content=f"✅ {new_item['name']}を削除しました。",
                                        view=items_view
                                    )
                            except Exception as e:
                                print(f"Error deleting item: {e}")
                                await button_interaction.response.send_message(
                                    "削除中にエラーが発生しました。",
                                    ephemeral=True
                                )
                    
                    delete_view = DeleteView()

                # アイテム一覧を表示
                items_view = GachaItemsView(self.settings, self.settings_manager)
                await interaction.response.edit_message(
                    content=f"✅ アイテムを{action}しました: {new_item['name']}",
                    view=items_view
                )

                # 削除ボタンを表示
                if delete_view:
                    await interaction.followup.send(
                        f"{new_item['name']}を削除:",
                        view=delete_view,
                        ephemeral=True
                    )
            
            else:
                await interaction.response.send_message(
                    "❌ 設定の更新に失敗しました。",
                    ephemeral=True
                )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ 設定エラー: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error updating gacha item: {e}")
            await interaction.response.send_message(
                "❌ エラーが発生しました。\n入力内容を確認してください。",
                ephemeral=True
            )

    async def _validate_url(self, url: str) -> tuple[bool, str]:
        """URLの有効性を検証する"""
        if not url.startswith(('http://', 'https://')):
            return False, "URLはhttp://またはhttps://で始まる必要があります"
        
        try:
            return True, ""
        except Exception as e:
            return False, str(e)

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