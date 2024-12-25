import discord
from discord.ext import commands
from discord import app_commands
from utils.automation_manager import AutomationManager
from typing import Optional, List
import traceback
import json

class RuleModal(discord.ui.Modal):
    def __init__(self, title: str = "新しいルール作成"):
        super().__init__(title=title)
        
        self.name = discord.ui.TextInput(
            label='ルール名',
            placeholder='例: VIPロール付与',
            required=True,
            max_length=100
        )
        self.add_item(self.name)
        
        self.description = discord.ui.TextInput(
            label='説明',
            placeholder='例: 1000ポイント達成でVIPロールを付与',
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        return {
            'name': self.name.value,
            'description': self.description.value
        }

class Automation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automation_manager = AutomationManager(bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            # メッセージイベントの処理
            await self.automation_manager.process_automation_rules(
                str(message.author.id),
                str(message.guild.id),
                'message',
                {'message_content': message.content}
            )
        except Exception as e:
            print(f"Error processing message automation: {e}")
            print(traceback.format_exc())

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        try:
            # メンバー更新イベントの処理
            await self.automation_manager.process_automation_rules(
                str(after.id),
                str(after.guild.id),
                'member_update',
                {
                    'before_roles': [str(r.id) for r in before.roles],
                    'after_roles': [str(r.id) for r in after.roles]
                }
            )
        except Exception as e:
            print(f"Error processing member update automation: {e}")
            print(traceback.format_exc())

    async def create_rule(self, interaction: discord.Interaction):
        modal = RuleModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        result = await modal.on_submit(interaction)
        if result:
            rule = await self.automation_manager.create_rule(
                str(interaction.guild_id),
                result['name'],
                result['description']
            )
            
            if rule:
                await interaction.followup.send(f"ルール「{result['name']}」を作成しました。")
            else:
                await interaction.followup.send("ルールの作成に失敗しました。")

    @app_commands.command(name="automation", description="自動化ルールを管理します")
    @app_commands.checks.has_permissions(administrator=True)
    async def automation(self, interaction: discord.Interaction, action: str, rule_id: Optional[str] = None):
        try:
            if action == "create":
                await self.create_rule(interaction)
                
            elif action == "list":
                rules = await self.automation_manager.get_server_rules(str(interaction.guild_id))
                if not rules:
                    await interaction.response.send_message("ルールが設定されていません。")
                    return
                
                embed = discord.Embed(title="自動化ルール一覧", color=discord.Color.blue())
                for rule in rules:
                    status = "✅ 有効" if rule.enabled else "❌ 無効"
                    embed.add_field(
                        name=f"{rule.name} ({status})",
                        value=f"ID: {rule.id}\n説明: {rule.description}",
                        inline=False
                    )
                await interaction.response.send_message(embed=embed)
                
            elif action == "delete" and rule_id:
                success = await self.automation_manager.delete_rule(str(interaction.guild_id), rule_id)
                if success:
                    await interaction.response.send_message(f"ルール（ID: {rule_id}）を削除しました。")
                else:
                    await interaction.response.send_message("ルールの削除に失敗しました。")
                    
            elif action == "toggle" and rule_id:
                success = await self.automation_manager.toggle_rule(str(interaction.guild_id), rule_id)
                if success:
                    await interaction.response.send_message(f"ルール（ID: {rule_id}）の状態を切り替えました。")
                else:
                    await interaction.response.send_message("ルールの状態変更に失敗しました。")
                    
            else:
                await interaction.response.send_message(
                    "使用可能なコマンド:\n"
                    "/automation create: 新しいルールを作成\n"
                    "/automation list: ルール一覧を表示\n"
                    "/automation delete <rule_id>: ルールを削除\n"
                    "/automation toggle <rule_id>: ルールの有効/無効を切り替え"
                )
        except Exception as e:
            print(f"Error in automation command: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("コマンドの実行中にエラーが発生しました。", ephemeral=True)

    @app_commands.command(name="automation-history", description="自動化ルールの実行履歴を表示します")
    @app_commands.checks.has_permissions(administrator=True)
    async def automation_history(self, interaction: discord.Interaction, limit: int = 10):
        try:
            history = await self.automation_manager.get_execution_history(str(interaction.guild_id), limit)
            if not history:
                await interaction.response.send_message("実行履歴がありません。")
                return

            embed = discord.Embed(title="自動化ルール実行履歴", color=discord.Color.blue())
            for entry in history:
                timestamp = discord.utils.format_dt(entry.executed_at)
                user = await self.bot.fetch_user(int(entry.user_id))
                user_name = user.name if user else entry.user_id
                
                embed.add_field(
                    name=f"{timestamp}",
                    value=f"ユーザー: {user_name}\n"
                          f"ルール: {entry.rule_name}\n"
                          f"結果: {'✅ 成功' if entry.success else '❌ 失敗'}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Error in automation history command: {e}")
            print(traceback.format_exc())
            await interaction.followup.send("履歴の取得中にエラーが発生しました。", ephemeral=True)

    @automation.error
    @automation_history.error
    async def automation_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        else:
            print(f"Unexpected error in automation commands: {error}")
            print(traceback.format_exc())
            await interaction.followup.send("予期せぬエラーが発生しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Automation(bot))