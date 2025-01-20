from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytz
import traceback
import discord  # discord importを追加
from decimal import Decimal  # Decimal importを追加
from models.automation_settings import (
    AutomationRule, Condition, Action, 
    ConditionType, ActionType, OperatorType
)

class AutomationManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_server_rules(self, server_id: str) -> List[AutomationRule]:
        """サーバーのルール一覧を取得"""
        try:
            rules_data = await self.db.get_automation_rules(server_id)
            for rule_data in rules_data:
                print(f"[DEBUG] Saved rule data: {rule_data}")
            return [AutomationRule.from_dict(rule) for rule in rules_data]
        except Exception as e:
            print(f"Error fetching server rules: {e}")
            print(traceback.format_exc())
            return []

    async def create_rule(self, server_id: str, name: str, description: str) -> Optional[AutomationRule]:
        """新しいルールを作成"""
        try:
            rule = AutomationRule.create_new(server_id, name, description)
            success = await self.db.save_automation_rule(rule.to_dict())
            return rule if success else None
        except Exception as e:
            print(f"Error creating rule: {e}")
            print(traceback.format_exc())
            return None

    async def update_rule(self, rule: AutomationRule) -> bool:
        """ルールを更新"""
        try:
            rule.updated_at = datetime.now(pytz.UTC).isoformat()
            return await self.db.save_automation_rule(rule.to_dict())
        except Exception as e:
            print(f"Error updating rule: {e}")
            print(traceback.format_exc())
            return False
        
    async def process_points_update(self, user_id: str, server_id: str, points: int, unit_id: str = "1"):
        """
        ポイント更新時の処理
        - unit_idに基づいて適切なポイント処理を行う
        """
        try:
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(server_id)
            if not settings:
                return

            # ポイント関連のルールを処理
            rules = await self.get_server_rules(server_id)
            for rule in rules:
                if not rule.enabled:
                    continue
                
                # ポイント閾値に関連するルールのみを処理
                point_conditions = [
                    cond for cond in rule.conditions 
                    if cond.type in [ConditionType.POINTS_THRESHOLD, ConditionType.POINTS_RANGE]
                ]
                
                if not point_conditions:
                    continue

                # unit_idを含むコンテキストデータを作成
                context_data = {
                    'user_id': user_id,
                    'server_id': server_id,
                    'points': points,
                    'unit_id': unit_id,
                    'type': 'points_update'
                }

                # 条件チェックにunit_idを含める
                conditions_met = await self._check_conditions(
                    rule.conditions, 
                    context_data
                )

                if conditions_met:
                    await self._execute_actions(
                        rule.actions,
                        context_data
                    )

        except Exception as e:
            print(f"Error processing points update: {e}")
            print(traceback.format_exc())

    async def _process_single_rule(self, rule: AutomationRule, data: Dict[str, Any]):
        """単一のルールを処理"""
        if not rule.enabled:
            return
            
        # クールダウンチェック
        if rule.cooldown and rule.last_triggered:
            last_time = datetime.fromisoformat(rule.last_triggered)
            if datetime.now(pytz.UTC) < last_time + timedelta(minutes=rule.cooldown):
                return

        # 条件チェック
        if not await self._check_conditions(rule.conditions, data):
            return

        # アクション実行
        success = await self._execute_actions(rule.actions, data)
        if success:
            rule.last_triggered = datetime.now(pytz.UTC).isoformat()
            await self.update_rule(rule)
            await self._log_execution(rule, data)

    async def _check_conditions(self, conditions: List[Condition], data: Dict[str, Any]) -> bool:
        """条件のチェック"""
        for condition in conditions:
            if not await self._check_single_condition(condition, data):
                return False
        return True

    async def _check_single_condition(self, condition: Condition, data: Dict[str, Any]) -> bool:
        """単一の条件をチェック - ポイント単位対応"""
        if condition.type == ConditionType.POINTS_THRESHOLD:
            points = data.get('points', 0)
            unit_id = data.get('unit_id', "1")
            
            # 条件のunit_idとデータのunit_idが一致する場合のみ処理
            if hasattr(condition, 'unit_id') and condition.unit_id != unit_id:
                return False

            print(f"Checking points threshold: current points = {points}, condition value = {condition.value}")

            if condition.operator == OperatorType.EQUALS:
                return points == condition.value
            elif condition.operator == OperatorType.GREATER_THAN:
                return points > condition.value
            elif condition.operator == OperatorType.LESS_THAN:
                return points < condition.value
            elif condition.operator == OperatorType.GREATER_EQUAL:
                return points >= condition.value
            elif condition.operator == OperatorType.LESS_EQUAL:
                return points <= condition.value
            elif condition.operator == OperatorType.BETWEEN:
                if isinstance(condition.value, list) and len(condition.value) == 2:
                    return condition.value[0] <= points <= condition.value[1]
                return False

        return False

    async def _execute_actions(self, actions: List[Action], data: Dict[str, Any]) -> bool:
        """アクションの実行"""
        try:
            for action in actions:
                print(f"[DEBUG] Executing action: {action}")
                print(f"[DEBUG] Action notification: {action.notification_settings}")  # notification の確認
                await self._execute_single_action(action, data)
            return True
        except Exception as e:
            print(f"Error executing actions: {e}")
            print(traceback.format_exc())
            return False
        
    async def send_notification(self, guild_id: str, user_id: str, role_id: str, channel_id: str, template: str):
        """通知を送信する"""
        try:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                print(f"Guild not found: {guild_id}")
                return

            channel = guild.get_channel(int(channel_id))
            if not channel:
                print(f"Channel not found: {channel_id}")
                return
            
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                print(f"User not found: {user_id}")
                return

            role = guild.get_role(int(role_id))
            if not role:
                print(f"Role not found: {role_id}")
                return
            
            # メッセージの変数を置換
            message = template.format(
                user_mention=user.mention,
                role_mention=role.mention,
                user_name=user.display_name,
                role_name=role.name
            )
            
            # 権限チェック
            bot_member = guild.get_me()
            if not channel.permissions_for(bot_member).send_messages:
                print(f"Bot does not have permission to send messages in {channel.name}")
                return
            
            await channel.send(message)
            
        except Exception as e:
            print(f"Notification error: {e}")
            print(traceback.format_exc())

    async def _execute_single_action(self, action: Action, data: Dict[str, Any]):
        """単一のアクションを実行"""
        try:
            guild = self.bot.get_guild(int(data['server_id']))
            if not guild:
                raise ValueError(f"Guild not found: {data['server_id']}")

            member = guild.get_member(int(data['user_id']))
            if not member:
                raise ValueError(f"Member not found: {data['user_id']}")

            # Botのメンバー情報を取得
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                raise ValueError("Bot is not in the guild")

            if action.type == ActionType.ADD_ROLE:
                role = guild.get_role(int(action.value))
                if not role:
                    raise ValueError(f"Role not found: {action.value}")
                
                # 権限チェック
                if not bot_member.guild_permissions.manage_roles:
                    print(f"Bot does not have manage roles permission in {guild.name}")
                    return
                    
                if bot_member.top_role <= role:
                    print(f"Bot's role ({bot_member.top_role.name}) is not high enough to assign {role.name}")
                    return
                
                await member.add_roles(role)

            elif action.type == ActionType.REMOVE_ROLE:
                role = guild.get_role(int(action.value))
                if not role:
                    raise ValueError(f"Role not found: {action.value}")
                    
                # 権限チェック
                if not bot_member.guild_permissions.manage_roles:
                    return
                    
                if bot_member.top_role <= role:
                    return
                    
                await member.remove_roles(role)

            elif action.type == ActionType.SEND_MESSAGE:
                if isinstance(action.value, dict) and 'channel_id' in action.value:
                    channel = guild.get_channel(int(action.value['channel_id']))
                    if channel:
                        await channel.send(action.value.get('content', ''))

            elif action.type == ActionType.GIVE_POINTS:
                if isinstance(action.value, (int, str)):
                    points_to_give = int(action.value)
                    current_points = data.get('points', 0)
                    await self.bot.db.update_user_points(
                        data['user_id'], 
                        data['server_id'],
                        current_points + points_to_give
                    )

            elif action.type == ActionType.SEND_NOTIFICATION:
                if action.notification_settings and action.notification_settings.enabled:
                    await self.send_notification(
                        guild_id=data['server_id'],
                        user_id=data['user_id'],
                        role_id=action.value if action.type == ActionType.ADD_ROLE else None,
                        channel_id=action.notification_settings.channel_id,
                        template=action.notification_settings.message_template
                    )

            # アクション完了後の通知処理
            if action.notification_settings and action.notification_settings.enabled:
                await self.send_notification(
                    guild_id=data['server_id'],
                    user_id=data['user_id'],
                    role_id=action.value if action.type == ActionType.ADD_ROLE else None,
                    channel_id=action.notification_settings.channel_id,
                    template=action.notification_settings.message_template
                )

        except discord.Forbidden as e:
            print(f"Permission error in {guild.name}: {e}")
        except Exception as e:
            print(f"Error executing action: {e}")
            print(traceback.format_exc())

    async def send_notification(self, guild_id: str, user_id: str, role_id: str, channel_id: str, template: str):
        """通知を送信する"""
        try:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                print(f"Guild not found: {guild_id}")
                return

            channel = guild.get_channel(int(channel_id))
            if not channel:
                print(f"Channel not found: {channel_id}")
                return
            
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                print(f"User not found: {user_id}")
                return

            role = guild.get_role(int(role_id))
            if not role:
                print(f"Role not found: {role_id}")
                return
            
            # メッセージの変数を置換
            message = template.format(
                user_mention=user.mention,
                role_mention=role.mention,
                user_name=user.display_name,
                role_name=role.name
            )
            
            # guild.get_me() を guild.me に変更
            bot_member = guild.me
            if not channel.permissions_for(bot_member).send_messages:
                print(f"Bot does not have permission to send messages in {channel.name}")
                return
            
            await channel.send(message)
            
        except Exception as e:
            print(f"Notification error: {e}")
            print(traceback.format_exc())
            
    # async def _log_execution(self, rule: AutomationRule, data: Dict[str, Any]):
    #     """ルール実行のログを記録"""
    #     try:
    #         await self.db.save_automation_history({
    #             'server_id': rule.server_id,
    #             'rule_id': rule.id,
    #             'user_id': data['user_id'],
    #             'trigger_type': data.get('type'),
    #             'executed_at': datetime.now(pytz.UTC).isoformat(),
    #             'data': data
    #         })
    #     except Exception as e:
    #         print(f"Error logging execution: {e}")
    #         print(traceback.format_exc())

    async def process_automation_rules(
        self,
        user_id: str,
        server_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """
        自動化ルールを処理
        Args:
            user_id: ユーザーID
            server_id: サーバーID
            event_type: イベントタイプ（'member_update', 'message'など）
            event_data: イベント関連データ
        """
        try:
            rules = await self.get_server_rules(server_id)
            for rule in rules:
                if not rule.enabled:
                    continue

                # イベントタイプに基づいてルールを処理
                await self._process_single_rule(rule, {
                    'user_id': user_id,
                    'server_id': server_id,
                    'type': event_type,
                    **event_data
                })

        except Exception as e:
            print(f"Error processing {event_type} automation: {e}")
            print(traceback.format_exc())