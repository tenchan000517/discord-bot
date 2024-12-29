'use client';

import React from 'react';
import { EditableFeatureCard } from '../EditableFeatureCard';
import { ServerSettingsForm } from '../EditForms/ServerSettingsForm';
import { Settings, Bell, CoinsIcon } from 'lucide-react';

const ServerSettings = ({
    serverData,
    serverSettings,
    selectedServer,
    editingSection,
    setEditingSection,
    handleUpdateSettings,
    saving
}) => {
    const handleSettingsUpdate = async (newSettings) => {
        try {
            const updatedSettings = {
                ...serverData.settings,
                global_settings: {
                    ...serverData.settings.global_settings,
                    ...newSettings
                }
            };
            await handleUpdateSettings('server-settings', updatedSettings);
        } catch (error) {
            console.error('Error updating server settings:', error);
        }
    };

    return (
        <EditableFeatureCard
            title="サーバー設定"
            isEditing={editingSection === 'server-settings'}
            onEditToggle={() =>
                setEditingSection(
                    editingSection === 'server-settings' ? null : 'server-settings'
                )
            }
            onSave={(data) => handleUpdateSettings('server-settings', data)}
            editForm={
                <ServerSettingsForm
                    settings={serverData.settings}
                    onSubmit={(data) => handleUpdateSettings('server-settings', data)}
                />
            }
        >
            <div className="p-6">
                <div className="flex items-center gap-3 mb-6">
                    <Settings className="w-5 h-5 text-gray-400" />
                    <h2 className="text-xl font-medium">基本設定</h2>
                </div>

                {/* サーバー情報 */}
                <div className="mb-8">
                    <h3 className="text-lg font-medium mb-4">サーバー情報</h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                        <div>
                            <p className="text-sm font-medium text-gray-700">サーバーID</p>
                            <p className="text-gray-600">{selectedServer?.id}</p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700">作成日</p>
                            <p className="text-gray-600">
                                {serverData?.created_at
                                    ? new Date(serverData.created_at).toLocaleString('ja-JP')
                                    : '不明'}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700">メンバー数</p>
                            <p className="text-gray-600">
                                {selectedServer?.member_count?.toLocaleString() || '不明'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* ポイント設定 */}
                <div className="mb-8">
                    <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                        <CoinsIcon className="w-5 h-5 text-gray-400" />
                        ポイント設定
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                        <div>
                            <p className="text-sm font-medium text-gray-700">ポイント単位</p>
                            <p className="text-gray-600">{serverSettings?.point_unit || 'pt'}</p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700">日次獲得上限</p>
                            <p className="text-gray-600">
                                {serverSettings?.daily_point_limit?.toLocaleString() || '制限なし'}{' '}
                                {serverSettings?.point_unit || 'pt'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* 通知設定 */}
                <div>
                    <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                        <Bell className="w-5 h-5 text-gray-400" />
                        通知設定
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                        <div>
                            <p className="text-sm font-medium text-gray-700">ポイント獲得通知</p>
                            <p className="text-gray-600">
                                {serverSettings?.notifications?.points_earned ? '有効' : '無効'}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700">ランキング更新通知</p>
                            <p className="text-gray-600">
                                {serverSettings?.notifications?.ranking_updated ? '有効' : '無効'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </EditableFeatureCard>
    );
};

export default ServerSettings;
