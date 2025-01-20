from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional, Literal
import logging
from .settings.views.token_view import TokenSettingsView
from contracts.wallet_connect import WalletConnectManager
from utils.token_operations import TokenOperations
from web3 import Web3
import io  # これを追加してください

logger = logging.getLogger(__name__)

class TokenTransfer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wallet_manager = WalletConnectManager()
        self.token_operations = TokenOperations()

    @app_commands.command(name="wallet")
    @app_commands.describe(
        action="実行するアクション（connect/disconnect/status）"
    )
    async def wallet(
        self, 
        interaction: discord.Interaction, 
        action: Literal["connect", "disconnect", "status"]
    ):
        """ウォレット関連のコマンド"""
        await interaction.response.defer(ephemeral=True)

        try:
            if action == "connect":
                # すでに接続されているか確認
                if self.wallet_manager.is_connected(str(interaction.user.id)):
                    await interaction.followup.send("すでにウォレットは接続されています。", ephemeral=True)
                    return

                # 新規セッション作成
                session_id, qr_bytes = await self.wallet_manager.create_session(str(interaction.user.id))
                
                # QRコードをファイルとして送信
                qr_file = discord.File(
                    io.BytesIO(qr_bytes), 
                    filename="wallet_connect.png",
                    description="Wallet Connect QR Code"
                )

                await interaction.followup.send(
                    content="以下のQRコードをスキャンしてウォレットを接続してください。",
                    file=qr_file,
                    ephemeral=True  # 必要に応じて変更
                )
                
                # 接続待ち
                try:
                    wallet_address = await self.wallet_manager.handle_connection(str(interaction.user.id))
                    if wallet_address:
                        await interaction.followup.send(
                            f"ウォレットが接続されました！\nアドレス: {wallet_address}", 
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send(
                            "ウォレット接続がタイムアウトしました。もう一度お試しください。",
                            ephemeral=True
                        )
                except Exception as e:
                    logger.error(f"ウォレット接続中にエラー: {e}")
                    await interaction.followup.send(
                        "ウォレット接続中にエラーが発生しました。管理者にお問い合わせください。",
                        ephemeral=True
                    )


            elif action == "disconnect":
                await self.wallet_manager.disconnect(str(interaction.user.id))
                await interaction.followup.send("ウォレットを切断しました。", ephemeral=True)

            elif action == "status":
                session = await self.wallet_manager.get_active_session(str(interaction.user.id))
                if session and session.connected:
                    await interaction.followup.send(
                        f"接続中のウォレット: {session.accounts[0]}", 
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "ウォレットは接続されていません。", 
                        ephemeral=True
                    )

        except Exception as e:
            logger.error(f"Wallet command error: {str(e)}")
            await interaction.followup.send(
                "エラーが発生しました。もう一度お試しください。", 
                ephemeral=True
            )

    @app_commands.command(name="transfer")
    @app_commands.describe(
        to="送信先のウォレットアドレス",
        amount="送信するトークンの量"
    )
    async def transfer(
        self, 
        interaction: discord.Interaction, 
        to: str, 
        amount: float
    ):
        """トークンを転送します"""
        await interaction.response.defer(ephemeral=True)

        try:
            # ウォレット接続確認
            session = await self.wallet_manager.get_active_session(str(interaction.user.id))
            if not session or not session.connected:
                await interaction.followup.send(
                    "ウォレットが接続されていません。先に /wallet connect を実行してください。",
                    ephemeral=True
                )
                return

            # サーバーのトークン設定を取得
            token_settings = await self.token_operations.get_token_settings(str(interaction.guild.id))
            if not token_settings or not token_settings.get('enabled'):
                await interaction.followup.send(
                    "このサーバーではトークン転送が設定されていません。",
                    ephemeral=True
                )
                return

            # Web3インスタンスの作成
            web3 = Web3(Web3.HTTPProvider(token_settings['rpcUrl']))
            
            # 残高確認
            balance = await self.token_operations.get_balance(
                web3,
                token_settings['contractAddress'],
                session.accounts[0]
            )
            
            if balance is None or balance < amount:
                await interaction.followup.send(
                    f"残高が不足しています。(残高: {balance} {token_settings['tokenSymbol']})",
                    ephemeral=True
                )
                return

            # トランザクション実行
            tx_hash = await self.token_operations.transfer_tokens(
                web3,
                token_settings['contractAddress'],
                session.accounts[0],
                to,
                amount,
                session.private_key  # WalletConnectから取得
            )

            if tx_hash:
                await interaction.followup.send(
                    f"転送が完了しました！\nTransaction Hash: {tx_hash}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "転送に失敗しました。もう一度お試しください。",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Transfer error: {str(e)}")
            await interaction.followup.send(
                "エラーが発生しました。もう一度お試しください。",
                ephemeral=True
            )

    @app_commands.command(name="token_settings")
    @app_commands.default_permissions(administrator=True)
    async def token_settings(self, interaction: discord.Interaction):
        """トークン設定を開く（管理者のみ）"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "この操作には管理者権限が必要です。", 
                ephemeral=True
            )
            return

        view = TokenSettingsView(self.bot)
        await view.start(interaction)

async def setup(bot):
    await bot.add_cog(TokenTransfer(bot))