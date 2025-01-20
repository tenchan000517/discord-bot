import discord
from .base import BaseSettingsModal  # 正しい
from typing import Optional
from web3 import Web3
import logging
from utils.token_operations import TokenOperations
from typing import Any  # この行を追加

logger = logging.getLogger(__name__)

class TokenSettingsModal(BaseSettingsModal):
    def __init__(self, settings: Any = None):  # デフォルト値を設定
        super().__init__(title="トークン設定", settings=settings)
        self.token_operations = TokenOperations()
        
        # フィールドの追加
        self.add_item(
            discord.ui.TextInput(
                label="ネットワークID",
                placeholder="例: 1 (Ethereum Mainnet)",
                required=True,
                max_length=10
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="RPC URL",
                placeholder="例: https://eth-mainnet.public.blastapi.io",
                required=True
            )
        )

        self.add_item(
            discord.ui.TextInput(
                label="コントラクトアドレス",
                placeholder="0x...",
                required=True,
                max_length=42
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="トークンシンボル",
                placeholder="例: ETH",
                required=True,
                max_length=10
            )
        )
        
        self.add_item(
            discord.ui.TextInput(
                label="デシマル",
                placeholder="例: 18",
                required=True,
                max_length=2
            )
        )

    async def validate_inputs(self) -> Optional[str]:
        """入力値の検証"""
        try:
            # ネットワークIDの検証
            network_id = int(self.children[0].value)
            if network_id <= 0:
                return "無効なネットワークIDです。"

            # RPCのURLの検証
            if not self.children[1].value.startswith(("http://", "https://")):
                return "無効なRPC URLです。"

            # コントラクトアドレスの検証
            if not Web3.is_address(self.children[2].value):
                return "無効なコントラクトアドレスです。"

            # デシマルの検証
            decimals = int(self.children[4].value)
            if not (0 <= decimals <= 18):
                return "デシマルは0から18の間で指定してください。"

            return None

        except ValueError:
            return "数値の入力形式が正しくありません。"
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return "入力値の検証中にエラーが発生しました。"

    async def on_submit(self, interaction: discord.Interaction):
        """設定の保存"""
        try:
            # 入力値の検証
            error_message = await self.validate_inputs()
            if error_message:
                await interaction.response.send_message(
                    f"エラー: {error_message}", 
                    ephemeral=True
                )
                return

            # 設定の保存
            success = await self.token_operations.update_token_settings(
                server_id=str(interaction.guild_id),
                network_id=int(self.children[0].value),
                rpc_url=self.children[1].value,
                contract_address=self.children[2].value,
                token_symbol=self.children[3].value,
                decimals=int(self.children[4].value)
            )

            if success:
                await interaction.response.send_message(
                    "トークン設定を保存しました。", 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "設定の保存に失敗しました。", 
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Token settings save error: {str(e)}")
            await interaction.response.send_message(
                "設定の保存中にエラーが発生しました。", 
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """エラーハンドリング"""
        logger.error(f"Token settings modal error: {str(error)}")
        await interaction.response.send_message(
            "エラーが発生しました。もう一度お試しください。",
            ephemeral=True
        )