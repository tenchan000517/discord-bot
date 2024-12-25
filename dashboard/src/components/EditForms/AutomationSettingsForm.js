import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { Alert } from '@/components/ui/Alert';
import NotificationSettings from './NotificationSettings';

const ConditionType = {
    POINTS_THRESHOLD: 'points_threshold',
    MESSAGE_COUNT: 'message_count',
    REACTION_COUNT: 'reaction_count',
    TIME_CONDITION: 'time_condition',
    NOTIFICATION_TRIGGER: 'notification_trigger'  // 追加
};

const ActionType = {
    ADD_ROLE: 'add_role',
    REMOVE_ROLE: 'remove_role',
    SEND_MESSAGE: 'send_message',
    GIVE_POINTS: 'give_points',
    SEND_NOTIFICATION: 'send_notification'  // 追加
};

const OperatorType = {
    EQUALS: 'equals',
    GREATER_THAN: 'greater_than',
    LESS_THAN: 'less_than',
    GREATER_EQUAL: 'greater_equal',
    LESS_EQUAL: 'less_equal'
};

export const AutomationSettingsForm = ({
    settings,
    pointUnit,
    serverId,  // <- props として受け取る
    onChange,
    onSubmit,
    serverRoles = [],
    serverData = {} // 追加
}) => {
    const [formState, setFormState] = useState({
        rules: settings?.rules || [],
        enabled: settings?.enabled || false,
        isValid: true,
        errors: []
    });
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    const updateFormState = (updates) => {
        setFormState(current => {
            const newState = { ...current, ...updates };
            const validation = validateForm(newState);
            return { ...newState, ...validation };
        });
    };

    const validateForm = (state) => {
        const errors = [];

        if (state.rules.length > 0) {
            state.rules.forEach((rule, index) => {
                if (!rule.name) {
                    errors.push(`ルール${index + 1}の名前は必須です`);
                }
                if (!rule.conditions || rule.conditions.length === 0) {
                    errors.push(`ルール${index + 1}には少なくとも1つの条件が必要です`);
                }
                if (!rule.actions || rule.actions.length === 0) {
                    errors.push(`ルール${index + 1}には少なくとも1つのアクションが必要です`);
                }
            });
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    };

    const handleAddRule = async () => {
        const newRule = {
            id: `rule_${Date.now()}`,
            name: '',
            description: '',
            enabled: true,
            server_id: serverId,
            conditions: [{
                type: ConditionType.POINTS_THRESHOLD,
                operator: OperatorType.GREATER_EQUAL,
                value: 0
            }],
            actions: [{
                type: ActionType.ADD_ROLE,
                value: '',
                parameters: {}
            }]
        };

        try {
            const response = await fetch(`/api/servers/${serverId}/automation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newRule),
            });

            if (!response.ok) {
                throw new Error('ルールの作成に失敗しました');
            }

            const updatedRules = [...formState.rules, newRule];
            updateFormState({ rules: updatedRules });

            if (onChange) {
                onChange({
                    enabled: formState.enabled,
                    rules: updatedRules,
                    isValid: true,
                    errors: []
                });
            }
        } catch (error) {
            console.error('Error adding rule:', error);
            setFormState(prev => ({
                ...prev,
                errors: [...prev.errors, 'ルールの作成に失敗しました']
            }));
        }
    };

    const handleUpdateRule = async (ruleId, field, value) => {
        try {
            const updatedRules = formState.rules.map(rule =>
                rule.id === ruleId ? { ...rule, [field]: value } : rule
            );

            const targetRule = updatedRules.find(r => r.id === ruleId);
            console.log(`[DEBUG] Updated rule:`, targetRule); // ここでルール全体を確認
            console.log(`[DEBUG] Notification field in rule:`, targetRule?.notification); // notificationフィールドの確認

            if (!targetRule) {
                throw new Error('Rule not found');
            }

            const response = await fetch(`/api/servers/${serverId}/automation`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    server_id: serverId,
                    id: ruleId,
                    ...targetRule
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to update rule');
            }

            updateFormState({ rules: updatedRules });
            if (onChange) {
                onChange({
                    enabled: formState.enabled,
                    rules: updatedRules,
                    isValid: true,
                    errors: []
                });
            }
        } catch (error) {
            console.error('Error updating rule:', error);
            setFormState(prev => ({
                ...prev,
                errors: [...prev.errors, 'ルールの更新に失敗しました']
            }));
        }
    };

    // 有効/無効の切り替え
    const handleToggleRule = async (ruleId) => {
        try {
            const updatedRules = formState.rules.map(rule => {
                if (rule.id === ruleId) {
                    return { ...rule, enabled: !rule.enabled };
                }
                return rule;
            });

            // 該当ルールを取得
            const targetRule = updatedRules.find(r => r.id === ruleId);
            if (!targetRule) {
                throw new Error('Rule not found');
            }

            console.log('Toggle rule request:', {
                serverId,  // <-- window.location の代わりにpropsから受け取ったものを使用
                ruleId,
                currentRules: formState.rules
            });

            // 完全なルール情報を送信
            const response = await fetch(`/api/servers/${serverId}/automation`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    server_id: serverId,
                    id: ruleId,
                    name: targetRule.name,
                    description: targetRule.description,
                    enabled: targetRule.enabled,
                    conditions: targetRule.conditions,
                    actions: targetRule.actions,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to update rule status');
            }

            // 成功したら状態を更新
            updateFormState({ rules: updatedRules });
        } catch (error) {
            console.error('Error toggling rule:', error);
            // エラー時は状態を元に戻す
            setFormState(prev => ({
                ...prev,
                rules: prev.rules.map(rule => {
                    if (rule.id === ruleId) {
                        return { ...rule, enabled: !rule.enabled }; // トグル前の状態に戻す
                    }
                    return rule;
                }),
                errors: [...prev.errors, 'ルールの更新に失敗しました']
            }));
        }
    };

    // ルールの削除
    const handleDeleteRule = async (ruleId) => {
        try {
            const response = await fetch(`/api/servers/${serverId}/automation?ruleId=${ruleId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Failed to delete rule');
            }

            // 成功したら状態から削除
            const updatedRules = formState.rules.filter(rule => rule.id !== ruleId);
            updateFormState({ rules: updatedRules });
            setDeleteConfirm(null);
        } catch (error) {
            console.error('Error deleting rule:', error);
            setFormState(prev => ({
                ...prev,
                errors: [...prev.errors, 'ルールの削除に失敗しました']
            }));
        }
    };

    const handleRuleChange = (ruleId, field, value) => {
        console.log(`[DEBUG] handleRuleChange called for ruleId: ${ruleId}, field: ${field}, value:`, value); // ログ追加

        updateFormState({
            rules: formState.rules.map(rule =>
                rule.id === ruleId ? { ...rule, [field]: value } : rule
            )
        });
        console.log(`[DEBUG] Updated formState.rules:`, formState.rules); // 更新後の状態確認

    };

    const handleConditionChange = (ruleId, condIndex, field, value) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId) {
                    const newConditions = [...rule.conditions];
                    newConditions[condIndex] = {
                        ...newConditions[condIndex],
                        [field]: field === 'value' ? parseInt(value) || 0 : value
                    };
                    return { ...rule, conditions: newConditions };
                }
                return rule;
            })
        });
    };

    const handleAddCondition = (ruleId) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId) {
                    return {
                        ...rule,
                        conditions: [...rule.conditions, {
                            type: ConditionType.POINTS_THRESHOLD,
                            operator: OperatorType.GREATER_EQUAL,
                            value: 0
                        }]
                    };
                }
                return rule;
            })
        });
    };

    const handleDeleteCondition = (ruleId, condIndex) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId && rule.conditions.length > 1) {
                    const newConditions = [...rule.conditions];
                    newConditions.splice(condIndex, 1);
                    return { ...rule, conditions: newConditions };
                }
                return rule;
            })
        });
    };

    const handleActionChange = (ruleId, actionIndex, field, value) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId) {
                    const newActions = [...rule.actions];
                    newActions[actionIndex] = {
                        ...newActions[actionIndex],
                        [field]: field === 'value' && newActions[actionIndex].type === ActionType.GIVE_POINTS ?
                            parseInt(value) || 0 : value
                    };
                    return { ...rule, actions: newActions };
                }
                return rule;
            })
        });
    };

    const handleAddAction = (ruleId) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId) {
                    return {
                        ...rule,
                        actions: [...rule.actions, {
                            type: ActionType.ADD_ROLE,
                            value: '',
                            parameters: {}
                        }]
                    };
                }
                return rule;
            })
        });
    };

    const handleDeleteAction = (ruleId, actionIndex) => {
        updateFormState({
            rules: formState.rules.map(rule => {
                if (rule.id === ruleId && rule.actions.length > 1) {
                    const newActions = [...rule.actions];
                    newActions.splice(actionIndex, 1);
                    return { ...rule, actions: newActions };
                }
                return rule;
            })
        });
    };

    useEffect(() => {
        if (typeof onSubmit === 'function') {
            const submitHandler = () => {
                console.log('AutomationSettingsForm - Submitting FormState:', formState);
                return {
                    rules: formState.rules,
                    enabled: formState.enabled,
                    server_id: serverId
                };
            };

            onSubmit(submitHandler);
        }
    }, [formState, serverId, onSubmit]);

    useEffect(() => {
        if (onChange) {
            onChange({
                enabled: formState.enabled,
                rules: formState.rules,
                isValid: formState.isValid,
                errors: formState.errors
            });
        }
    }, [formState, onChange]);

    useEffect(() => {
        console.log(`[DEBUG] Current formState.rules:`, JSON.stringify(formState.rules, null, 2));
    }, [formState.rules]);

    return (
        <div className="space-y-4">
            {formState.errors.length > 0 && (
                <div className="bg-red-50 p-4 rounded-lg">
                    {formState.errors.map((error, index) => (
                        <div key={index} className="text-red-700">{error}</div>
                    ))}
                </div>
            )}

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <span className="font-medium">オートメーションを有効化</span>
                <div className="relative inline-block w-10 align-middle select-none">
                    <input
                        type="checkbox"
                        checked={formState.enabled}
                        onChange={(e) => updateFormState({ enabled: e.target.checked })}
                        className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                    />
                    <label className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer" />
                </div>
            </div>

            {formState.rules.map((rule, index) => (
                <div key={rule.id} className="border rounded-lg p-4">
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="space-y-2 flex-1 mr-4">
                                <label className="block text-sm font-medium text-gray-700">ルール名</label>
                                <input
                                    type="text"
                                    value={rule.name}
                                    onChange={(e) => handleRuleChange(rule.id, 'name', e.target.value)}
                                    placeholder="ルール名を入力"
                                    className="w-full px-3 py-2 border rounded-md"
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                {/* 有効/無効切り替えボタン */}
                                <button
                                    onClick={() => handleToggleRule(rule.id)}
                                    className={`p-2 rounded-md ${rule.enabled
                                        ? 'text-green-600 hover:text-green-700'
                                        : 'text-gray-400 hover:text-gray-500'
                                        }`}
                                    title={rule.enabled ? '無効にする' : '有効にする'}
                                >
                                    {rule.enabled ? (
                                        <ToggleRight className="h-5 w-5" />
                                    ) : (
                                        <ToggleLeft className="h-5 w-5" />
                                    )}
                                </button>

                                {/* 削除ボタン */}
                                {deleteConfirm === rule.id ? (
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => handleDeleteRule(rule.id)}
                                            className="px-2 py-1 bg-red-600 text-white rounded-md text-sm"
                                        >
                                            削除する
                                        </button>
                                        <button
                                            onClick={() => setDeleteConfirm(null)}
                                            className="px-2 py-1 bg-gray-200 text-gray-700 rounded-md text-sm"
                                        >
                                            キャンセル
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setDeleteConfirm(rule.id)}
                                        className="p-2 text-gray-400 hover:text-red-600"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">説明</label>
                            <input
                                type="text"
                                value={rule.description}
                                onChange={(e) => handleRuleChange(rule.id, 'description', e.target.value)}
                                placeholder="ルールの説明を入力"
                                className="w-full px-3 py-2 border rounded-md mt-1"
                            />
                        </div>

                        {rule.conditions.map((condition, condIndex) => (
                            <div key={condIndex} className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">条件 {condIndex + 1}</label>
                                <div className="grid grid-cols-3 gap-2">
                                    <select
                                        value={condition.type}
                                        onChange={(e) => handleConditionChange(rule.id, condIndex, 'type', e.target.value)}
                                        className="w-full px-3 py-2 border rounded-md"
                                    >
                                        <option value={ConditionType.POINTS_THRESHOLD}>ポイント条件</option>
                                        <option value={ConditionType.MESSAGE_COUNT}>メッセージ数</option>
                                        <option value={ConditionType.REACTION_COUNT}>リアクション数</option>
                                        <option value={ConditionType.TIME_CONDITION}>時間条件</option>
                                    </select>
                                    <select
                                        value={condition.operator}
                                        onChange={(e) => handleConditionChange(rule.id, condIndex, 'operator', e.target.value)}
                                        className="w-full px-3 py-2 border rounded-md"
                                    >
                                        <option value={OperatorType.EQUALS}>等しい</option>
                                        <option value={OperatorType.GREATER_THAN}>より大きい</option>
                                        <option value={OperatorType.LESS_THAN}>より小さい</option>
                                        <option value={OperatorType.GREATER_EQUAL}>以上</option>
                                        <option value={OperatorType.LESS_EQUAL}>以下</option>
                                    </select>
                                    <input
                                        type="number"
                                        value={condition.value}
                                        onChange={(e) => handleConditionChange(rule.id, condIndex, 'value', e.target.value)}
                                        placeholder="値を入力"
                                        className="w-full px-3 py-2 border rounded-md"
                                    />
                                </div>
                                <button
                                    onClick={() => handleDeleteCondition(rule.id, condIndex)}
                                    className="text-sm text-red-600 hover:text-red-800"
                                >
                                    条件を削除
                                </button>
                            </div>
                        ))}
                        <button
                            onClick={() => handleAddCondition(rule.id)}
                            className="text-sm text-blue-600 hover:text-blue-800"
                        >
                            条件を追加
                        </button>

                        {rule.actions.map((action, actionIndex) => (
                            <div key={actionIndex} className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">アクション {actionIndex + 1}</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <select
                                        value={action.type}
                                        onChange={(e) => handleActionChange(rule.id, actionIndex, 'type', e.target.value)}
                                        className="w-full px-3 py-2 border rounded-md"
                                    >
                                        <option value={ActionType.ADD_ROLE}>ロール付与</option>
                                        <option value={ActionType.REMOVE_ROLE}>ロール剥奪</option>
                                        <option value={ActionType.SEND_MESSAGE}>メッセージ送信</option>
                                        <option value={ActionType.GIVE_POINTS}>ポイント付与</option>
                                        <option value={ActionType.SEND_NOTIFICATION}>通知送信</option>  {/* 追加 */}
                                    </select>
                                    {(action.type === ActionType.ADD_ROLE || action.type === ActionType.REMOVE_ROLE) ? (
                                        <select
                                            value={action.value}
                                            onChange={(e) => handleActionChange(rule.id, actionIndex, 'value', e.target.value)}
                                            className="w-full px-3 py-2 border rounded-md"
                                        >
                                            <option value="">ロールを選択</option>
                                            {serverRoles.map((role) => (
                                                <option key={role.id} value={role.id}>{role.name}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            type={action.type === ActionType.GIVE_POINTS ? "number" : "text"}
                                            value={action.value}
                                            onChange={(e) => handleActionChange(rule.id, actionIndex, 'value', e.target.value)}
                                            placeholder={action.type === ActionType.GIVE_POINTS ? "ポイント数を入力" : "メッセージ内容を入力"}
                                            className="w-full px-3 py-2 border rounded-md"
                                        />
                                    )}
                                </div>
                                <button
                                    onClick={() => handleDeleteAction(rule.id, actionIndex)}
                                    className="text-sm text-red-600 hover:text-red-800"
                                >
                                    アクションを削除
                                </button>
                            </div>
                        ))}
                        <button
                            onClick={() => handleAddAction(rule.id)}
                            className="text-sm text-blue-600 hover:text-blue-800"
                        >
                            アクションを追加
                        </button>

                        {/* 通知設定を追加 */}
                        <NotificationSettings
                            notification={rule.notification}
                            channels={serverData?.channels || []}
                            onUpdate={(notificationSettings) =>
                                handleRuleChange(rule.id, 'notification', notificationSettings)
                            }
                        />
                    </div>
                </div>
            ))}
            <button
                onClick={handleAddRule}
                className="inline-flex items-center px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
                <Plus className="mr-2 h-4 w-4" />
                新しいルールを追加
            </button>
        </div>
    );
};

export default AutomationSettingsForm;