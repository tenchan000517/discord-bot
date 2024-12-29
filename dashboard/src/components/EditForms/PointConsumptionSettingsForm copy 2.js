import React from 'react';
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

    const handleChange = (field, value) => {
        console.log('handleChange called:', { field, value });

        const newSettings = {
            ...settings,
            [field]: value
        };
        console.log('New Settings:', newSettings);

        onChange(newSettings);
    };

    const handleLoggingActionToggle = (action) => {
        const currentActions = settings.logging_actions || [];
        const newActions = currentActions.includes(action)
            ? currentActions.filter(a => a !== action)
            : [...currentActions, action];
        handleChange('logging_actions', newActions);
    };

    const handleRoleSelection = (roleId) => {
        const currentRoles = settings.mention_role_ids || [];
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
                                checked={settings.enabled}
                                onCheckedChange={(checked) => handleChange('enabled', checked)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>ボタン表示名</Label>
                            <Input
                                value={settings.button_name || 'ポイント消費'}
                                onChange={(e) => handleChange('button_name', e.target.value)}
                                placeholder="ボタンの表示名を入力"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>必要ポイント数</Label>
                            <Input
                                type="number"
                                value={settings.required_points || 0}
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
                                value={settings.display_channel_id || ''}
                                onChange={(e) => {
                                    console.log('Select onChange event:', e);
                                    console.log('Selected value:', e.target.value);
                                    handleChange('display_channel_id', e.target.value);
                                }}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels?.map((channel) => {
                                    // console.log('Rendering channel option:', channel);
                                    return (
                                        <option key={channel.id} value={channel.id}>
                                            {channel.name}
                                        </option>
                                    );
                                })}
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>通知チャンネル</Label>
                            <Select
                                value={settings.notification_channel_id || ''}
                                onChange={(e) => {
                                    console.log('Select onChange event:', e);
                                    console.log('Selected value:', e.target.value);
                                    handleChange('notification_channel_id', e.target.value);
                                }}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels?.map((channel) => {
                                    // console.log('Rendering channel option:', channel);
                                    return (
                                        <option key={channel.id} value={channel.id}>
                                            {channel.name}
                                        </option>
                                    );
                                })}
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
                                        variant={settings.mention_role_ids?.includes(role.id) ? "default" : "outline"}
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
                                checked={settings.use_thread}
                                onCheckedChange={(checked) => handleChange('use_thread', checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between">
                            <Label>完了メッセージを表示</Label>
                            <Switch
                                checked={settings.completion_message_enabled}
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
                                checked={settings.logging_enabled}
                                onCheckedChange={(checked) => handleChange('logging_enabled', checked)}
                            />
                        </div>

                        {settings.logging_enabled && (
                            <>
                                <div className="space-y-2">
                                    <Label>ログチャンネル</Label>
                                    <Select
                                        value={settings.logging_channel_id || ''}
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
                                                    checked={settings.logging_actions?.includes(action.id)}
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