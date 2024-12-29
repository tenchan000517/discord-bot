import React, { useState, useEffect } from 'react';  // useStateとuseEffectを追加
import { Card, CardContent } from '@/components/ui/Card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';

export const PointConsumptionSettingsForm = ({
    settings = {},
    serverData,
    onChange,
    serverRoles = [],
    pointUnit = 'pt',
}) => {
    const channels = serverData?.channels || [];

    // コンポーネント内で状態を管理
    const [formData, setFormData] = useState({
        enabled: settings.enabled || false,
        button_name: settings.button_name || 'ポイント消費',
        display_channel_id: settings.display_channel_id || '',
        notification_channel_id: settings.notification_channel_id || '',
        mention_role_ids: settings.mention_role_ids || [],
        use_thread: settings.use_thread || false,
        completion_message_enabled: settings.completion_message_enabled || true,
        required_points: settings.required_points || 0,
        logging_enabled: settings.logging_enabled || false,
        logging_channel_id: settings.logging_channel_id || '',
        logging_actions: settings.logging_actions || []
    });

    // settings propの変更を監視
    useEffect(() => {
        setFormData({
            enabled: settings.enabled || false,
            button_name: settings.button_name || 'ポイント消費',
            display_channel_id: settings.display_channel_id || '',
            notification_channel_id: settings.notification_channel_id || '',
            mention_role_ids: settings.mention_role_ids || [],
            use_thread: settings.use_thread || false,
            completion_message_enabled: settings.completion_message_enabled || true,
            required_points: settings.required_points || 0,
            logging_enabled: settings.logging_enabled || false,
            logging_channel_id: settings.logging_channel_id || '',
            logging_actions: settings.logging_actions || []
        });
    }, [settings]);

    const handleChange = (field, value) => {
        const newFormData = {
            ...formData,
            [field]: value
        };
        setFormData(newFormData);
        onChange(newFormData);
    };

    const handleLoggingActionToggle = (action) => {
        const currentActions = formData.logging_actions;
        const newActions = currentActions.includes(action)
            ? currentActions.filter(a => a !== action)
            : [...currentActions, action];
        handleChange('logging_actions', newActions);
    };

    const handleRoleSelection = (roleId) => {
        const currentRoles = formData.mention_role_ids;
        const newRoles = currentRoles.includes(roleId)
            ? currentRoles.filter(id => id !== roleId)
            : [...currentRoles, roleId];
        handleChange('mention_role_ids', newRoles);
    };

    return (
        <div className="space-y-6">
            {/* 基本設定 */}
            <Card>
                <CardContent className="p-6">
                    <h3 className="text-lg font-medium mb-4">基本設定</h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label>機能の有効化</Label>
                            <Switch
                                checked={formData.enabled}
                                onCheckedChange={(checked) => handleChange('enabled', checked)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>ボタン表示名</Label>
                            <Input
                                value={formData.button_name}
                                onChange={(e) => handleChange('button_name', e.target.value)}
                                placeholder="ボタンの表示名を入力"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>必要ポイント数</Label>
                            <Input
                                type="number"
                                value={formData.required_points}
                                onChange={(e) => handleChange('required_points', parseInt(e.target.value, 10))}
                                placeholder={`必要な${pointUnit}を入力`}
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* チャンネル設定 */}
            <Card>
                <CardContent className="p-6">
                    <h3 className="text-lg font-medium mb-4">チャンネル設定</h3>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label>表示チャンネル</Label>
                            <Select
                                value={formData.display_channel_id}
                                onChange={(e) => {
                                    console.log('Select onChange event:', e);
                                    console.log('Selected value:', e.target.value);
                                    handleChange('display_channel_id', e.target.value);
                                }}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels?.map((channel) => (
                                    <option key={channel.id} value={channel.id}>
                                        {channel.name}
                                    </option>
                                ))}
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>通知チャンネル</Label>
                            <Select
                                value={formData.notification_channel_id}
                                onChange={(e) => {
                                    console.log('Select onChange event:', e);
                                    console.log('Selected value:', e.target.value);
                                    handleChange('notification_channel_id', e.target.value);
                                }}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels?.map((channel) => (
                                    <option key={channel.id} value={channel.id}>
                                        {channel.name}
                                    </option>
                                ))}
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 通知設定 */}
            <Card>
                <CardContent className="p-6">
                    <h3 className="text-lg font-medium mb-4">通知設定</h3>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label>メンションロール</Label>
                            <div className="grid grid-cols-2 gap-2">
                                {serverRoles?.map((role) => (
                                    <Button
                                        key={role.id}
                                        variant={formData.mention_role_ids?.includes(role.id) ? "default" : "outline"}
                                        onClick={() => handleRoleSelection(role.id)}
                                        className="justify-start"
                                    >
                                        {role.name}
                                    </Button>
                                ))}
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <Label>スレッドを使用</Label>
                            <Switch
                                checked={formData.use_thread}
                                onCheckedChange={(checked) => handleChange('use_thread', checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between">
                            <Label>完了メッセージを表示</Label>
                            <Switch
                                checked={formData.completion_message_enabled}
                                onCheckedChange={(checked) => handleChange('completion_message_enabled', checked)}
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* ログ設定 */}
            <Card>
                <CardContent className="p-6">
                    <h3 className="text-lg font-medium mb-4">ログ設定</h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label>ログ機能を有効化</Label>
                            <Switch
                                checked={formData.logging_enabled}
                                onCheckedChange={(checked) => handleChange('logging_enabled', checked)}
                            />
                        </div>

                        {formData.logging_enabled && (
                            <>
                                <div className="space-y-2">
                                    <Label>ログチャンネル</Label>
                                    <Select
                                        value={formData.logging_channel_id}
                                        onChange={(e) => handleChange('logging_channel_id', e.target.value)}
                                    >
                                        <option value="">チャンネルを選択</option>
                                        {channels?.map((channel) => (
                                            <option key={channel.id} value={channel.id}>
                                                {channel.name}
                                            </option>
                                        ))}
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label>記録するアクション</Label>
                                    <div className="space-y-2">
                                        {[
                                            { id: 'click', label: 'ボタンクリック' },
                                            { id: 'complete', label: '完了' },
                                            { id: 'cancel', label: 'キャンセル' }
                                        ].map((action) => (
                                            <div key={action.id} className="flex items-center justify-between">
                                                <span className="text-sm">{action.label}</span>
                                                <Switch
                                                    checked={formData.logging_actions?.includes(action.id)}
                                                    onCheckedChange={() => handleLoggingActionToggle(action.id)}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default PointConsumptionSettingsForm;