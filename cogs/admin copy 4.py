import discord
from discord import app_commands
from discord.ext import commands
import traceback

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup_consumption",
        description="ポイント消費パネルを設置します"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_consumption(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        """ポイント消費パネルのセットアップを行います"""
        try:
            print(f"[DEBUG] setup_consumption command initiated")
            print(f"[DEBUG] User: {interaction.user.id}, Channel: {channel.id}")
            
            # 処理開始時に応答を遅延
            await interaction.response.defer(ephemeral=True)
            print("[DEBUG] Response deferred")
            
            try:
                print("[DEBUG] Attempting to get server settings...")
                settings = await self.bot.get_server_settings(str(interaction.guild_id))
                print(f"[DEBUG] Settings retrieved: {settings is not None}")
                
                if not settings or not settings.point_consumption_settings:
                    print("[DEBUG] Settings validation failed")
                    await interaction.followup.send(
                        "サーバーの設定が見つかりません。",
                        ephemeral=True
                    )
                    return

                print("[DEBUG] Checking for PointsConsumption cog...")
                point_consumption_cog = self.bot.get_cog('PointsConsumption')
                print(f"[DEBUG] Cog found: {point_consumption_cog is not None}")

                if not point_consumption_cog:
                    print("[DEBUG] PointsConsumption cog not found")
                    await interaction.followup.send(
                        "ポイント消費機能が利用できません。",
                        ephemeral=True
                    )
                    return

                print("[DEBUG] Starting panel setup...")
                try:
                    await point_consumption_cog.setup_consumption_panel(
                        str(channel.id),
                        settings
                    )
                    print("[DEBUG] Panel setup completed successfully")
                except Exception as panel_error:
                    print(f"[ERROR] Panel setup failed: {panel_error}")
                    print(traceback.format_exc())
                    await interaction.followup.send(
                        f"パネルの設置中にエラーが発生しました。\nError: {str(panel_error)}",
                        ephemeral=True
                    )
                    return

                # 成功時のメッセージ
                print("[DEBUG] Sending success message")
                await interaction.followup.send(
                    f"✅ ポイント消費パネルを {channel.mention} に設置しました。",
                    ephemeral=True
                )
                print("[DEBUG] Success message sent")

            except Exception as inner_error:
                print(f"[ERROR] Inner error: {inner_error}")
                print(traceback.format_exc())
                await interaction.followup.send(
                    f"⚠️ 処理中にエラーが発生しました。\nError: {str(inner_error)}",
                    ephemeral=True
                )

        except Exception as e:
            print(f"[ERROR] Outer error in setup_consumption: {e}")
            print(f"[ERROR] Error type: {type(e)}")
            print("[ERROR] Full traceback:")
            print(traceback.format_exc())
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"⚠️ 重大なエラーが発生しました。\nError: {str(e)}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⚠️ 重大なエラーが発生しました。\nError: {str(e)}",
                        ephemeral=True
                    )
            except Exception as final_error:
                print(f"[ERROR] Failed to send error message: {final_error}")

    @app_commands.command(
        name="debug_bot",
        description="Botの状態をデバッグします"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def debug_bot(self, interaction: discord.Interaction):
        """Botの状態を診断するデバッグコマンド"""
        try:
            debug_info = []
            debug_info.append("=== Bot Debug Information ===")
            
            # 基本情報
            debug_info.append("\n【基本情報】")
            debug_info.append(f"Bot User ID: {self.bot.user.id}")
            debug_info.append(f"Guild ID: {interaction.guild_id}")
            debug_info.append(f"Channel ID: {interaction.channel_id}")
            
            # データベース状態
            debug_info.append("\n【データベース状態】")
            debug_info.append(f"Database Available: {self.bot.db_available}")
            
            # サーバー設定
            debug_info.append("\n【サーバー設定】")
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            debug_info.append(f"Settings Found: {settings is not None}")
            if settings:
                debug_info.append(f"Point Consumption Settings: {settings.point_consumption_settings is not None}")
                if settings.point_consumption_settings:
                    debug_info.append(f"- Enabled: {settings.point_consumption_settings.enabled}")
                    debug_info.append(f"- Panel Title: {settings.point_consumption_settings.panel_title}")
            
            # Cogの状態
            debug_info.append("\n【Cog状態】")
            for cog_name in ['Admin', 'PointsConsumption']:
                cog = self.bot.get_cog(cog_name)
                debug_info.append(f"{cog_name}: {'✅ Loaded' if cog else '❌ Not Loaded'}")
            
            # コマンド状態
            debug_info.append("\n【登録済みコマンド】")
            commands = self.bot.tree.get_commands()
            for cmd in commands:
                debug_info.append(f"- /{cmd.name}")
            
            # 権限状態
            debug_info.append("\n【Bot権限】")
            permissions = interaction.guild.me.guild_permissions
            debug_info.append(f"Administrator: {permissions.administrator}")
            debug_info.append(f"Manage Channels: {permissions.manage_channels}")
            debug_info.append(f"Send Messages: {permissions.send_messages}")
            debug_info.append(f"Create Public Threads: {permissions.create_public_threads}")
            debug_info.append(f"Create Private Threads: {permissions.create_private_threads}")
            debug_info.append(f"Manage Messages: {permissions.manage_messages}")
            debug_info.append(f"Embed Links: {permissions.embed_links}")
            
            # デバッグ情報を送信
            debug_text = "\n".join(debug_info)
            
            # 長いメッセージを分割して送信
            chunks = [debug_text[i:i+1900] for i in range(0, len(debug_text), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.response.send_message(f"```{chunk}```", ephemeral=True)
                else:
                    await interaction.followup.send(f"```{chunk}```", ephemeral=True)

        except Exception as e:
            print(f"[ERROR] Error in debug_bot: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                f"デバッグ中にエラーが発生しました。\nError: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Admin(bot))