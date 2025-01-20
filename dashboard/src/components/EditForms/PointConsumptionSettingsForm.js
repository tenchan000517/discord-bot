// src/components/EditForms/PointConsumptionSettingsForm.js
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Settings, MessageSquare, Bell, Shield, History, ListTodo, LayoutDashboard } from 'lucide-react';

const TabButton = ({ active, onClick, children, icon: Icon }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${active
                ? 'bg-blue-100 text-blue-700'
                : 'hover:bg-gray-100 text-gray-600'
            }`}
    >
        <Icon className="w-4 h-4" />
        <span>{children}</span>
    </button>
);

const SettingsSection = ({ title, children }) => (
    <div className="space-y-4">
        <h3 className="font-medium text-lg">{title}</h3>
        {children}
    </div>
);

const FormField = ({ label, children, hint }) => (
    <div className="space-y-2">
        <Label>{label}</Label>
        {children}
        {hint && <p className="text-sm text-gray-500">{hint}</p>}
    </div>
);

export const PointConsumptionSettingsForm = ({
    settings = {},
    serverData,
    onChange,
    serverRoles = [],
    pointUnit = 'pt',
}) => {
    const [activeTab, setActiveTab] = useState('basic');
    const channels = serverData?.channels || [];

    const handleChange = (field, value) => {
        onChange({
            ...settings,
            [field]: value
        });
    };

    const handleModalSettingsChange = (section, field, value) => {
        const newModalSettings = {
            ...settings.modal_settings,
            [section]: {
                ...settings.modal_settings?.[section],
                [field]: value
            }
        };
        handleChange('modal_settings', newModalSettings);
    };

    const renderBasicSettings = () => (
        <SettingsSection title="基本設定">
            <div className="grid gap-6">
                <div className="flex items-center justify-between">
                    <Label>機能の有効化</Label>
                    <Switch
                        checked={settings.enabled}
                        onCheckedChange={checked => handleChange('enabled', checked)}
                    />
                </div>

                <FormField label="ボタン表示名">
                    <Input
                        value={settings.button_name}
                        onChange={e => handleChange('button_name', e.target.value)}
                        placeholder="ボタンの表示名を入力"
                    />
                </FormField>

                <FormField label="必要ポイント数">
                    <Input
                        type="number"
                        value={settings.required_points}
                        onChange={e => handleChange('required_points', parseInt(e.target.value))}
                        placeholder={`必要な${pointUnit}を入力`}
                    />
                </FormField>

                <FormField label="パネルタイトル">
                    <Input
                        value={settings.panel_title}
                        onChange={e => handleChange('panel_title', e.target.value)}
                        placeholder="パネルのタイトルを入力"
                    />
                </FormField>

                <FormField label="パネルメッセージ">
                    <Textarea
                        value={settings.panel_message}
                        onChange={e => handleChange('panel_message', e.target.value)}
                        placeholder="パネルのメッセージを入力"
                    />
                </FormField>

                <FormField label="表示チャンネル">
                    <Select
                        value={settings.channel_id}
                        onChange={e => handleChange('channel_id', e.target.value)}
                    >
                        <option value="">チャンネルを選択</option>
                        {channels.map(channel => (
                            <option key={channel.id} value={channel.id}>
                                {channel.name}
                            </option>
                        ))}
                    </Select>
                </FormField>
            </div>
        </SettingsSection>
    );

    const renderNotificationSettings = () => (
        <SettingsSection title="通知設定">
            <div className="grid gap-6">
                <FormField label="通知チャンネル">
                    <Select
                        value={settings.notification_channel_id}
                        onChange={e => handleChange('notification_channel_id', e.target.value)}
                    >
                        <option value="">チャンネルを選択</option>
                        {channels.map(channel => (
                            <option key={channel.id} value={channel.id}>
                                {channel.name}
                            </option>
                        ))}
                    </Select>
                </FormField>

                <FormField label="メンションロール">
                    <Select
                        multiple
                        value={settings.mention_role_ids}
                        onChange={e => {
                            const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                            handleChange('mention_role_ids', selectedOptions);
                        }}
                    >
                        {serverRoles.map(role => (
                            <option key={role.id} value={role.id}>{role.name}</option>
                        ))}
                    </Select>
                </FormField>

                <div className="flex items-center justify-between">
                    <Label>スレッドを使用</Label>
                    <Switch
                        checked={settings.use_thread}
                        onCheckedChange={checked => handleChange('use_thread', checked)}
                    />
                </div>

                {settings.use_thread && (
                    <FormField
                        label="スレッド初期メッセージ"
                        hint="利用可能な変数: {user}, {points}, {unit}"
                    >
                        <Textarea
                            value={settings.thread_welcome_message}
                            onChange={e => handleChange('thread_welcome_message', e.target.value)}
                            placeholder="スレッドの初期メッセージを入力"
                        />
                    </FormField>
                )}

                <FormField
                    label="通知メッセージ"
                    hint="利用可能な変数: {user}, {points}, {unit}"
                >
                    <Textarea
                        value={settings.notification_message}
                        onChange={e => handleChange('notification_message', e.target.value)}
                        placeholder="通知メッセージを入力"
                    />
                </FormField>

                <div className="flex items-center justify-between">
                    <Label>完了メッセージを表示</Label>
                    <Switch
                        checked={settings.completion_message_enabled}
                        onCheckedChange={checked => handleChange('completion_message_enabled', checked)}
                    />
                </div>

                {settings.completion_message_enabled && (
                    <FormField
                        label="完了メッセージ"
                        hint="利用可能な変数: {user}, {points}, {unit}, {admin}"
                    >
                        <Textarea
                            value={settings.completion_message}
                            onChange={e => handleChange('completion_message', e.target.value)}
                            placeholder="完了時のメッセージを入力"
                        />
                    </FormField>
                )}
            </div>
        </SettingsSection>
    );

    const renderApprovalSettings = () => (
        <SettingsSection title="承認設定">
            <div className="grid gap-6">
                <FormField label="承認可能なロール">
                    <Select
                        multiple
                        value={settings.approval_roles}
                        onChange={e => {
                            const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                            handleChange('approval_roles', selectedOptions);
                        }}
                    >
                        {serverRoles.map(role => (
                            <option key={role.id} value={role.id}>{role.name}</option>
                        ))}
                    </Select>
                </FormField>

                <div className="flex items-center justify-between">
                    <Label>管理者は常に承認可能</Label>
                    <Switch
                        checked={settings.admin_override}
                        onCheckedChange={checked => handleChange('admin_override', checked)}
                    />
                </div>
            </div>
        </SettingsSection>
    );

    const renderHistorySettings = () => (
        <SettingsSection title="履歴設定">
            <div className="grid gap-6">
                <div className="flex items-center justify-between">
                    <Label>履歴機能を有効化</Label>
                    <Switch
                        checked={settings.history_enabled}
                        onCheckedChange={checked => handleChange('history_enabled', checked)}
                    />
                </div>

                {settings.history_enabled && (
                    <>
                        <FormField label="履歴チャンネル">
                            <Select
                                value={settings.history_channel_id}
                                onChange={e => handleChange('history_channel_id', e.target.value)}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels.map(channel => (
                                    <option key={channel.id} value={channel.id}>{channel.name}</option>
                                ))}
                            </Select>
                        </FormField>

                        <FormField
                            label="履歴メッセージフォーマット"
                            hint="利用可能な変数: {user}, {points}, {unit}, {status}"
                        >
                            <Textarea
                                value={settings.history_format}
                                onChange={e => handleChange('history_format', e.target.value)}
                                placeholder="履歴メッセージのフォーマットを入力"
                            />
                        </FormField>
                    </>
                )}

                <div className="flex items-center justify-between">
                    <Label>獲得履歴を有効化</Label>
                    <Switch
                        checked={settings.gain_history_enabled}
                        onCheckedChange={checked => handleChange('gain_history_enabled', checked)}
                    />
                </div>

                {settings.gain_history_enabled && (
                    <FormField label="獲得履歴チャンネル">
                        <Select
                            value={settings.gain_history_channel_id}
                            onChange={e => handleChange('gain_history_channel_id', e.target.value)}
                        >
                            <option value="">チャンネルを選択</option>
                            {channels.map(channel => (
                                <option key={channel.id} value={channel.id}>{channel.name}</option>
                            ))}
                        </Select>
                    </FormField>
                )}

                <div className="flex items-center justify-between">
                    <Label>消費履歴を有効化</Label>
                    <Switch
                        checked={settings.consumption_history_enabled}
                        onCheckedChange={checked => handleChange('consumption_history_enabled', checked)}
                    />
                </div>

                {settings.consumption_history_enabled && (
                    <FormField label="消費履歴チャンネル">
                        <Select
                            value={settings.consumption_history_channel_id}
                            onChange={e => handleChange('consumption_history_channel_id', e.target.value)}
                        >
                            <option value="">チャンネルを選択</option>
                            {channels.map(channel => (
                                <option key={channel.id} value={channel.id}>{channel.name}</option>
                            ))}
                        </Select>
                    </FormField>
                )}
            </div>
        </SettingsSection>
    );

    const renderLogSettings = () => (
        <SettingsSection title="ログ設定">
            <div className="grid gap-6">
                <div className="flex items-center justify-between">
                    <Label>ログ機能を有効化</Label>
                    <Switch
                        checked={settings.logging_enabled}
                        onCheckedChange={checked => handleChange('logging_enabled', checked)}
                    />
                </div>

                {settings.logging_enabled && (
                    <>
                        <FormField label="ログチャンネル">
                            <Select
                                value={settings.logging_channel_id}
                                onChange={e => handleChange('logging_channel_id', e.target.value)}
                            >
                                <option value="">チャンネルを選択</option>
                                {channels.map(channel => (
                                    <option key={channel.id} value={channel.id}>{channel.name}</option>
                                ))}
                            </Select>
                        </FormField>

                        <div className="space-y-2">
                            <Label>記録するアクション</Label>
                            <div className="space-y-2 bg-gray-50 p-4 rounded-lg">
                                {[
                                    { id: 'click', label: 'ボタンクリック' },
                                    { id: 'complete', label: '完了' },
                                    { id: 'cancel', label: 'キャンセル' }
                                ].map(action => (
                                    <div key={action.id} className="flex items-center justify-between">
                                        <span className="text-sm">{action.label}</span>
                                        <Switch
                                            checked={settings.logging_actions?.includes(action.id)}
                                            onCheckedChange={() => {
                                                const newActions = settings.logging_actions?.includes(action.id)
                                                    ? settings.logging_actions.filter(a => a !== action.id)
                                                    : [...(settings.logging_actions || []), action.id];
                                                handleChange('logging_actions', newActions);
                                            }}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </SettingsSection>
    );

    const renderModalSettings = () => (
        <SettingsSection title="モーダル設定">
            <div className="grid gap-6">
                <FormField label="モーダルタイトル">
                    <Input
                        value={settings.modal_settings?.title}
                        onChange={e => handleModalSettingsChange('title', e.target.value)}
                        placeholder="モーダルのタイトルを入力"
                    />
                </FormField>

                <div className="space-y-4">
                    <Label>表示するフィールド</Label>
                    {Object.entries(settings.modal_settings?.fields || {}).map(([field, enabled]) => (
                        <div key={field} className="flex items-center justify-between">
                            <span className="text-sm">{field}</span>
                            <Switch
                                checked={enabled}
                                onCheckedChange={checked =>
                                    handleModalSettingsChange('fields', field, checked)
                                }
                            />
                        </div>
                    ))}
                </div>

                {Object.entries(settings.modal_settings?.fields || {}).map(([field, enabled]) =>
                    enabled && (
                        <div key={field} className="space-y-4 p-4 bg-gray-50 rounded-lg">
                            <h4 className="font-medium">{field}フィールドの設定</h4>

                            <FormField label="ラベル">
                                <Input
                                    value={settings.modal_settings?.field_labels?.[field]}
                                    onChange={e =>
                                        handleModalSettingsChange('field_labels', field, e.target.value)
                                    }
                                    placeholder={`${field}フィールドのラベル`}
                                />
                            </FormField>

                            <FormField label="プレースホルダー">
                                <Input
                                    value={settings.modal_settings?.field_placeholders?.[field]}
                                    onChange={e => handleModalSettingsChange('field_placeholders', field, e.target.value)}
                                    placeholder={`${field}フィールドのプレースホルダー`}
                                />
                            </FormField>

                            {field === 'points' && (
                                <div className="grid grid-cols-2 gap-4">
                                    <FormField label="最小値">
                                        <Input
                                            type="number"
                                            value={settings.modal_settings?.validation?.points?.min}
                                            onChange={e => {
                                                const newValidation = {
                                                    ...settings.modal_settings?.validation,
                                                    points: {
                                                        ...settings.modal_settings?.validation?.points,
                                                        min: parseInt(e.target.value)
                                                    }
                                                };
                                                handleModalSettingsChange('validation', newValidation);
                                            }}
                                        />
                                    </FormField>

                                    <FormField label="最大値">
                                        <Input
                                            type="number"
                                            value={settings.modal_settings?.validation?.points?.max || ''}
                                            onChange={e => {
                                                const newValidation = {
                                                    ...settings.modal_settings?.validation,
                                                    points: {
                                                        ...settings.modal_settings?.validation?.points,
                                                        max: e.target.value ? parseInt(e.target.value) : null
                                                    }
                                                };
                                                handleModalSettingsChange('validation', newValidation);
                                            }}
                                        />
                                    </FormField>
                                </div>
                            )}

                            {(field === 'wallet' || field === 'email') && (
                                <FormField label="バリデーションパターン">
                                    <Input
                                        value={settings.modal_settings?.validation?.[field]?.pattern}
                                        onChange={e => {
                                            const newValidation = {
                                                ...settings.modal_settings?.validation,
                                                [field]: {
                                                    pattern: e.target.value
                                                }
                                            };
                                            handleModalSettingsChange('validation', newValidation);
                                        }}
                                        placeholder="正規表現パターン"
                                    />
                                </FormField>
                            )}
                        </div>
                    )
                )}

                <FormField label="成功メッセージ">
                    <Input
                        value={settings.modal_settings?.success_message}
                        onChange={e => handleModalSettingsChange('success_message', e.target.value)}
                        placeholder="申請成功時のメッセージ"
                    />
                </FormField>
            </div>
        </SettingsSection>
    );

    return (
        <div className="space-y-6">
            {/* タブナビゲーション */}
            <div className="flex flex-wrap gap-2 border-b pb-2">
                <TabButton
                    active={activeTab === 'basic'}
                    onClick={() => setActiveTab('basic')}
                    icon={Settings}
                >
                    基本設定
                </TabButton>
                <TabButton
                    active={activeTab === 'notification'}
                    onClick={() => setActiveTab('notification')}
                    icon={Bell}
                >
                    通知設定
                </TabButton>
                <TabButton
                    active={activeTab === 'approval'}
                    onClick={() => setActiveTab('approval')}
                    icon={Shield}
                >
                    承認設定
                </TabButton>
                <TabButton
                    active={activeTab === 'history'}
                    onClick={() => setActiveTab('history')}
                    icon={ListTodo}
                >
                    履歴設定
                </TabButton>
                <TabButton
                    active={activeTab === 'log'}
                    onClick={() => setActiveTab('log')}
                    icon={History}
                >
                    ログ設定
                </TabButton>
                <TabButton
                    active={activeTab === 'modal'}
                    onClick={() => setActiveTab('modal')}
                    icon={LayoutDashboard}
                >
                    モーダル設定
                </TabButton>
            </div>

            {/* タブコンテンツ */}
            <div className="bg-white rounded-lg p-6">
                {activeTab === 'basic' && renderBasicSettings()}
                {activeTab === 'notification' && renderNotificationSettings()}
                {activeTab === 'approval' && renderApprovalSettings()}
                {activeTab === 'history' && renderHistorySettings()}
                {activeTab === 'log' && renderLogSettings()}
                {activeTab === 'modal' && renderModalSettings()}
            </div>
        </div>
    );
};

export default PointConsumptionSettingsForm;