'use client';

import React, { useMemo } from 'react';
import { EditableFeatureCard } from '../EditableFeatureCard';
import { BattleSettingsForm } from '../EditForms/BattleSettingsForm';
import { GachaSettingsForm } from '../EditForms/GachaSettingsForm';
import { FortuneSettingsForm } from '../EditForms/FortuneSettingsForm';
import { RewardsSettingsForm } from '../EditForms/RewardsSettingsForm';
import { AutomationSettingsForm } from '../EditForms/AutomationSettingsForm';
import { ServerSettingsForm } from '../EditForms/ServerSettingsForm';
import { Settings, Bell, Coins as CoinsIcon, Globe, Languages, Swords, Gift, Stars, Award, CreditCard } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { PointConsumptionSettingsForm } from '../EditForms/PointConsumptionSettingsForm';

const FeatureSettings = ({
    serverData,
    featureData,
    setFeatureData,
    editingSection,
    setEditingSection,
    handleUpdateSettings,
    calculateTotalWeight,
    automationRules,
    setAutomationRules,
    changeHistory,
    setChangeHistory,
    selectedServerId,
    selectedServer,  // 追加
    handleUpdateAutomationRule,
    setSaving,
    setError,
    serverRoles,
    selectedMenu,
    setServerData,
    channels, // channelsを追加
}) => {
    const featureSettingsData = useMemo(() => {
        if (!serverData?.settings) return null;
        const { feature_settings, global_settings } = serverData.settings;

        // 必須項目のチェックを削除し、feature_settingsの存在確認のみに変更
        if (!feature_settings) return null;

        return {
            battle: feature_settings.battle,
            gacha: feature_settings.gacha,
            fortune: feature_settings.fortune,
            rewards: feature_settings.rewards,
            point_consumption: feature_settings.point_consumption,  // デフォルト値を削除
            server: global_settings
        };
    }, [serverData]);

    if (!featureSettingsData) return null;
    const { battle, gacha, fortune, rewards, point_consumption, server } = featureSettingsData;

    const handleFeatureUpdate = async (feature, data) => {
        console.log('handleFeatureUpdate - feature:', feature);
        console.log('handleFeatureUpdate - data:', data);
        try {
            setSaving(true);
            let updatedSettings;

            // featureをスネークケースに正規化
            const normalizedFeature = feature.replace(/-/g, '_');

            if (feature === 'server-settings') {
                updatedSettings = {
                    ...serverData.settings,
                    global_settings: featureData.global_settings
                };
            } else {
                // feature_settingsが存在しない場合は空オブジェクトを使用
                const currentFeatureSettings = serverData.settings.feature_settings || {};

                updatedSettings = {
                    ...serverData.settings,
                    feature_settings: {
                        ...currentFeatureSettings,
                        [normalizedFeature]: data
                    }
                };
            }

            console.log('handleFeatureUpdate - Updated Settings:', updatedSettings);

            await handleUpdateSettings(
                feature === 'server-settings' ? 'server-settings' : 'feature-settings',
                updatedSettings
            );

            setEditingSection(null);
        } catch (error) {
            console.error('Error updating feature:', error);
            setError('設定の更新に失敗しました');
        } finally {
            setSaving(false);
        }
    };


    const handleServerSettingsChange = (updatedSettings) => {
        console.log('ローカル更新: updatedSettings', updatedSettings);
        setServerData((prev) => {
            const newData = {
                ...prev,
                settings: updatedSettings,
            };
            console.log('ローカル更新後: serverData', newData);
            return newData;
        });
    };


    // メニュー選択に基づいてコンテンツを表示
    const renderContent = () => {
        switch (selectedMenu) {
            case 'server-settings':
                return (
                    <EditableFeatureCard
                        title="サーバー設定"
                        isEditing={editingSection === 'server-settings'}
                        onEditToggle={() => setEditingSection(
                            editingSection === 'server-settings' ? null : 'server-settings'
                        )}
                        onSave={() => {
                            console.log('onSave triggered - data being passed:', featureData.global_settings);
                            handleFeatureUpdate('server-settings', featureData.global_settings);
                        }}
                        editForm={
                            <ServerSettingsForm
                                settings={serverData.settings}  // 元の構造に戻す
                                onChange={(formData) => {
                                    console.log('Form data changed:', formData);
                                    setFeatureData(prev => ({
                                        ...prev,
                                        global_settings: formData.global_settings
                                    }));
                                }}
                                onSubmit={(data) => handleFeatureUpdate('server-settings', data)}
                            />
                        }
                    >
                        {/* 表示コンテンツ */}
                        {/* <div className="p-6"> */}
                        <div className="space-y-6">
                            {/* 基本設定 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Settings className="w-5 h-5 text-gray-500" />
                                        基本設定
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {/* ポイント単位 */}
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Bell className="w-4 h-4 text-gray-500" />
                                                <h4 className="text-sm font-medium text-gray-500">ポイント単位</h4>
                                            </div>
                                            <p className="text-lg font-medium">
                                                {serverData.settings.global_settings.point_unit || 'pt'}
                                            </p>
                                        </div>

                                        {/* タイムゾーン */}
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Globe className="w-4 h-4 text-gray-500" />
                                                <h4 className="text-sm font-medium text-gray-500">タイムゾーン</h4>
                                            </div>
                                            <p className="text-lg font-medium">
                                                {serverData.settings.global_settings.timezone || 'Asia/Tokyo'}
                                            </p>
                                        </div>

                                        {/* 言語 */}
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Languages className="w-4 h-4 text-gray-500" />
                                                <h4 className="text-sm font-medium text-gray-500">言語</h4>
                                            </div>
                                            <p className="text-lg font-medium">
                                                {serverData.settings.global_settings.language === 'ja' ? '日本語' : 'English'}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* 機能設定状態 */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Settings className="w-5 h-5 text-gray-500" />
                                        機能設定
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {[
                                            { name: "バトル", icon: Swords, enabled: serverData.settings.feature_settings?.battle?.enabled },
                                            { name: "ガチャ", icon: Gift, enabled: serverData.settings.feature_settings?.gacha?.enabled },
                                            { name: "占い", icon: Stars, enabled: serverData.settings.feature_settings?.fortune?.enabled },
                                            { name: "報酬", icon: Award, enabled: serverData.settings.feature_settings?.rewards?.enabled },
                                            { name: "ポイント消費", icon: CreditCard, enabled: serverData.settings.feature_settings?.point_consumption?.enabled }
                                        ].map((feature) => (
                                            <div key={feature.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                                <div className="flex items-center gap-3">
                                                    <feature.icon className="w-5 h-5 text-gray-500" />
                                                    <span className="font-medium">{feature.name}</span>
                                                </div>
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${feature.enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                                                    }`}>
                                                    {feature.enabled ? "有効" : "無効"}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                        {/* </div> */}
                    </EditableFeatureCard>
                );

            case 'battle':
                return (
                    <EditableFeatureCard
                        title="バトル設定"
                        isEditing={editingSection === 'battle'}
                        onEditToggle={() => setEditingSection(editingSection === 'battle' ? null : 'battle')}
                        onSave={() => handleFeatureUpdate('battle', featureData.feature_settings.battle)}
                        editForm={
                            <BattleSettingsForm
                                settings={battle}
                                pointUnit={serverData.settings.global_settings.point_unit}
                                onChange={(data) => {
                                    setFeatureData({
                                        ...featureData,
                                        feature_settings: {
                                            ...featureData.feature_settings,
                                            battle: data
                                        }
                                    });
                                }}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-medium">バトル機能</h3>
                                    <p className="text-sm text-gray-500">バトル機能の設定を管理します</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${battle.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {battle.enabled ? "有効" : "無効"}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <p className="text-sm text-gray-500">キル報酬</p>
                                    <p className="font-medium">
                                        {battle.points_per_kill.toLocaleString()} {serverData.settings.global_settings.point_unit}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">勝者報酬</p>
                                    <p className="font-medium">
                                        {battle.winner_points.toLocaleString()} {serverData.settings.global_settings.point_unit}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">開始遅延</p>
                                    <p className="font-medium">{battle.start_delay_minutes}分</p>
                                </div>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );

            case 'gacha':
                return (
                    <EditableFeatureCard
                        title="ガチャ設定"
                        isEditing={editingSection === 'gacha'}
                        onEditToggle={() => setEditingSection(editingSection === 'gacha' ? null : 'gacha')}
                        onSave={() => handleFeatureUpdate('gacha', featureData.feature_settings.gacha)}
                        editForm={
                            <GachaSettingsForm
                                settings={gacha}
                                pointUnit={serverData.settings.global_settings.point_unit}
                                onChange={(data) => {
                                    setFeatureData({
                                        ...featureData,
                                        feature_settings: {
                                            ...featureData.feature_settings,
                                            gacha: data
                                        }
                                    });
                                }}
                                calculateTotalWeight={calculateTotalWeight}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-medium">ガチャ機能</h3>
                                    <p className="text-sm text-gray-500">ガチャ機能の設定を管理します</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${gacha.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {gacha.enabled ? "有効" : "無効"}
                                </span>
                            </div>

                            <div className="divide-y divide-gray-200">
                                {/* アイテム設定 */}
                                <div className="pb-6">
                                    <h4 className="text-base font-medium text-gray-900 mb-4">アイテム設定</h4>
                                    <div className="space-y-3">
                                        {gacha.items.map((item, index) => {
                                            const totalWeight = calculateTotalWeight(gacha.items);
                                            const probability = (parseInt(item.weight) / totalWeight * 100).toFixed(1);

                                            return (
                                                <div key={index} className="p-3 bg-gray-50 rounded-lg">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div>
                                                            <p className="font-medium">{item.name}</p>
                                                            <p className="text-sm text-gray-500">確率: {probability}%</p>
                                                        </div>
                                                        <p className="font-medium">{item.points.toLocaleString()} {serverData.settings.global_settings.point_unit}</p>
                                                    </div>
                                                    {/* メッセージ設定の表示 */}
                                                    {item.message_settings?.enabled && (
                                                        <div className="mt-2 pt-2 border-t border-gray-200">
                                                            <p className="text-sm text-gray-600">
                                                                <span className="text-gray-500">当選メッセージ: </span>
                                                                {item.message_settings.message || '設定なし'}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* メッセージ設定 */}
                                <div className="py-6">
                                    {/* <h4 className="text-base font-medium text-gray-900 mb-4">共通メッセージ設定</h4> */}
                                    <div className="space-y-4">
                                        {/* <div className="bg-gray-50 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-gray-700 mb-2">セットアップメッセージ</h5>
                                            <p className="text-gray-600">{gacha.messages?.setup || '設定なし'}</p>
                                        </div> */}
                                        <div className="bg-gray-50 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-gray-700 mb-2">デイリーメッセージ</h5>
                                            <p className="text-gray-600">{gacha.messages?.daily || '設定なし'}</p>
                                        </div>
                                        {/* X投稿メッセージの表示を追加 */}
                                        <div className="bg-gray-50 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-gray-700 mb-2">X投稿メッセージ</h5>
                                            <p className="text-gray-600">
                                                {gacha.messages?.tweet_message ? (
                                                    <span>
                                                        <span className="text-gray-400">デフォルト + </span>
                                                        {gacha.messages.tweet_message}
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-400">デフォルトのみ（ガチャ結果！ [アイテム名]を獲得！ +[ポイント数]ポイント獲得！）</span>
                                                )}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* メディア設定 */}
                                <div className="pt-6">
                                    <h4 className="text-base font-medium text-gray-900 mb-4">メディア設定</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-gray-50 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-gray-700 mb-2">セットアップ画像</h5>
                                            {gacha.media?.setup_image ? (
                                                <div className="mt-2">
                                                    <img
                                                        src={gacha.media.setup_image}
                                                        alt="Setup"
                                                        className="w-full h-auto rounded border border-gray-200"
                                                    />
                                                </div>
                                            ) : (
                                                <p className="text-gray-500 text-sm">設定なし</p>
                                            )}
                                        </div>
                                        <div className="bg-gray-50 p-4 rounded-lg">
                                            <h5 className="text-sm font-medium text-gray-700 mb-2">バナーGIF</h5>
                                            {gacha.media?.banner_gif ? (
                                                <div className="mt-2">
                                                    <img
                                                        src={gacha.media.banner_gif}
                                                        alt="Banner"
                                                        className="w-full h-auto rounded border border-gray-200"
                                                    />
                                                </div>
                                            ) : (
                                                <p className="text-gray-500 text-sm">設定なし</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );
            case 'fortune':
                return (
                    <EditableFeatureCard
                        title="占い設定"
                        isEditing={editingSection === 'fortune'}
                        onEditToggle={() => setEditingSection(editingSection === 'fortune' ? null : 'fortune')}
                        onSave={() => handleFeatureUpdate('fortune', featureData.feature_settings.fortune)}
                        editForm={
                            <FortuneSettingsForm
                                settings={fortune}
                                onChange={(data) => {
                                    setFeatureData({
                                        ...featureData,
                                        feature_settings: {
                                            ...featureData.feature_settings,
                                            fortune: data
                                        }
                                    });
                                }}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-medium">占い機能</h3>
                                    <p className="text-sm text-gray-500">占い機能の設定を管理します</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${fortune.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {fortune.enabled ? "有効" : "無効"}
                                </span>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );

            case 'rewards':
                return (
                    <EditableFeatureCard
                        title="報酬設定"
                        isEditing={editingSection === 'rewards'}
                        onEditToggle={() => setEditingSection(editingSection === 'rewards' ? null : 'rewards')}
                        onSave={() => handleFeatureUpdate('rewards', featureData.feature_settings.rewards)}
                        editForm={
                            <RewardsSettingsForm
                                settings={rewards}
                                pointUnit={serverData.settings.global_settings.point_unit}
                                onChange={(data) => {
                                    setFeatureData({
                                        ...featureData,
                                        feature_settings: {
                                            ...featureData.feature_settings,
                                            rewards: data
                                        }
                                    });
                                }}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-medium">報酬機能</h3>
                                    <p className="text-sm text-gray-500">報酬機能の設定を管理します</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${rewards?.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {rewards?.enabled ? "有効" : "無効"}
                                </span>
                            </div>

                            <div className="space-y-6">
                                {/* Web3設定の表示 */}
                                <div>
                                    <h4 className="text-base font-medium mb-3">Web3設定</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-sm text-gray-500">RPC URL</p>
                                            <p className="font-medium truncate">{rewards?.web3?.rpc_url || '未設定'}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-gray-500">NFTコントラクト</p>
                                            <p className="font-medium truncate">{rewards?.web3?.nft_contract_address || '未設定'}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* クーポンAPI設定の表示 */}
                                <div>
                                    <h4 className="text-base font-medium mb-3">クーポンAPI設定</h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        <div>
                                            <p className="text-sm text-gray-500">API URL</p>
                                            <p className="font-medium truncate">{rewards?.coupon_api?.api_url || '未設定'}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* 制限値設定の表示 */}
                                <div>
                                    <h4 className="text-base font-medium mb-3">制限値設定</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-sm text-gray-500">クーポン交換最小ポイント</p>
                                            <p className="font-medium">
                                                {rewards?.limits?.min_points_coupon?.toLocaleString() || '0'} {serverData.settings.global_settings.point_unit}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-gray-500">NFT発行最小ポイント</p>
                                            <p className="font-medium">
                                                {rewards?.limits?.min_points_nft?.toLocaleString() || '0'} {serverData.settings.global_settings.point_unit}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );

            case 'automation':
                return (
                    <EditableFeatureCard
                        title="オートメーション設定"
                        isEditing={editingSection === 'automation'}
                        onEditToggle={() => setEditingSection(editingSection === 'automation' ? null : 'automation')}
                        onSave={async () => {
                            setSaving(true);
                            try {
                                const payload = {
                                    enabled: Array.isArray(automationRules) && automationRules.length > 0,
                                    rules: automationRules || [],
                                    server_id: selectedServerId
                                };
                                await handleUpdateAutomationRule(null, payload);
                                setEditingSection(null);
                            } catch (error) {
                                console.error('Save error:', error);
                                setError(error.message);
                            } finally {
                                setSaving(false);
                            }
                        }}
                        editForm={
                            <AutomationSettingsForm
                                settings={{
                                    enabled: Array.isArray(automationRules) && automationRules.length > 0,
                                    rules: automationRules || [],
                                }}
                                pointUnit={serverData?.settings?.global_settings?.point_unit}
                                serverId={selectedServerId}
                                serverRoles={serverRoles}
                                serverData={serverData}
                                onChange={(formData) => {
                                    if (JSON.stringify(formData.rules) !== JSON.stringify(automationRules)) {
                                        setAutomationRules(formData.rules);
                                    }
                                    if (JSON.stringify(formData) !== JSON.stringify(changeHistory[0]?.changes)) {
                                        setChangeHistory(prev => [{
                                            timestamp: new Date(),
                                            section: 'automation',
                                            changes: formData,
                                        }, ...prev]);
                                    }
                                }}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="space-y-6">
                                <div className="flex justify-between items-center">
                                    <div>
                                        <h3 className="text-lg font-medium">オートメーション設定</h3>
                                        <p className="text-sm text-gray-500">自動化ルールの設定を管理します</p>
                                    </div>
                                </div>

                                {/* 既存ルール一覧の表示 */}
                                <div className="space-y-4">
                                    {!Array.isArray(automationRules) || automationRules.length === 0 ? (
                                        <p className="text-gray-500 text-center py-4">
                                            設定されているルールはありません
                                        </p>
                                    ) : (
                                        automationRules.map((rule) => (
                                            <div key={rule.id} className="bg-gray-50 p-4 rounded-lg">
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <h4 className="font-medium">{rule.name}</h4>
                                                        <p className="text-sm text-gray-600">{rule.description}</p>
                                                    </div>
                                                    <span className={`px-2 py-1 rounded-full text-sm ${rule.enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                                                        {rule.enabled ? "有効" : "無効"}
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );

            case 'point-consumption':
                return (
                    <EditableFeatureCard
                        title="ポイント消費設定"
                        isEditing={editingSection === 'point-consumption'}
                        onEditToggle={() => setEditingSection(editingSection === 'point-consumption' ? null : 'point-consumption')}
                        onSave={() => handleFeatureUpdate('point-consumption', featureData.feature_settings.point_consumption)}
                        editForm={
                            <PointConsumptionSettingsForm
                                settings={point_consumption}
                                serverData={serverData}
                                pointUnit={serverData.settings.global_settings.point_unit}
                                serverRoles={serverRoles}
                                onChange={(data) => {
                                    setFeatureData({
                                        ...featureData,
                                        feature_settings: {
                                            ...featureData.feature_settings,
                                            point_consumption: data
                                        }
                                    });
                                }}
                            />
                        }
                    >
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-lg font-medium">ポイント消費機能</h3>
                                    <p className="text-sm text-gray-500">ポイント消費機能の設定を管理します</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${point_consumption.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                    {point_consumption.enabled ? "有効" : "無効"}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <p className="text-sm text-gray-500">必要ポイント</p>
                                    <p className="font-medium">
                                        {point_consumption.required_points?.toLocaleString()} {server.point_unit}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">通知チャンネル</p>
                                    <p className="font-medium">
                                        {channels?.find(c => c.id === point_consumption.notification_channel_id)?.name || '未設定'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </EditableFeatureCard>
                );

            default:
                return null;
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-sm">
            <div className="p-0">
                {renderContent()}
            </div>
        </div>
    );
};

export default FeatureSettings;