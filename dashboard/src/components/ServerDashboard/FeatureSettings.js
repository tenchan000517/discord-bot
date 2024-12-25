'use client';

import React, { useMemo } from 'react';
import { Tab } from '@headlessui/react';
import { EditableFeatureCard } from '../EditableFeatureCard';
import FeatureSettingsWrapper from './FeatureSettingsWrapper'; // デフォルトインポート
import { AutomationSettingsForm } from '../EditForms/AutomationSettingsForm';

const FeatureSettings = ({
  serverData,
  featureData,
  setFeatureData,
  editingSection,
  setEditingSection,
  handleUpdateSettings,
  calculateTotalWeight,
  setSelectedTab,
  automationRules,
  automationHistory,
  setAutomationRules,
  changeHistory,
  setChangeHistory,
  selectedServerId,
  handleUpdateAutomationRule,
  setSaving,
  setError,
  serverRoles,
}) => {
  // メモ化したデータ
  const featureSettingsData = useMemo(() => {
    if (!serverData?.settings?.feature_settings) return null;

    const { battle, gacha, fortune } = serverData.settings.feature_settings;
    if (!battle || !gacha || !fortune) return null;

    return { battle, gacha, fortune };
  }, [serverData]);

  if (!featureSettingsData) return null;

  const { battle, gacha, fortune } = featureSettingsData;

  return (
    <EditableFeatureCard
    title="機能設定"
    isEditing={editingSection === 'feature-settings'}
    onEditToggle={() => setEditingSection(editingSection === 'feature-settings' ? null : 'feature-settings')}
    onSave={() => {
      if (featureData) {
        handleUpdateSettings('feature-settings', featureData);
      }
    }}
    editForm={
      <FeatureSettingsWrapper
        settings={serverData.settings}
        pointUnit={serverData.settings.global_settings.point_unit}
        onSubmit={setFeatureData}
      />
    }
  >
    <Tab.Group as="div" className="mt-8" onChange={setSelectedTab}>
      <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
        <Tab
          className={({ selected }) =>
            `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
            ${selected
              ? 'bg-white text-blue-700 shadow'
              : 'text-blue-500 hover:bg-white/[0.12] hover:text-blue-600'
            }`
          }
        >
          バトル設定
        </Tab>
        <Tab
          className={({ selected }) =>
            `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
            ${selected
              ? 'bg-white text-blue-700 shadow'
              : 'text-blue-500 hover:bg-white/[0.12] hover:text-blue-600'
            }`
          }
        >
          ガチャ設定
        </Tab>
        <Tab
          className={({ selected }) =>
            `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
            ${selected
              ? 'bg-white text-blue-700 shadow'
              : 'text-blue-500 hover:bg-white/[0.12] hover:text-blue-600'
            }`
          }
        >
          占い設定
        </Tab>
        {/* オートメーションタブを追加 */}
        <Tab
          className={({ selected }) =>
            `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
          ${selected
              ? 'bg-white text-blue-700 shadow'
              : 'text-blue-500 hover:bg-white/[0.12] hover:text-blue-600'
            }`
          }
        >
          オートメーション
        </Tab>
      </Tab.List>

      <Tab.Panels className="mt-4">
        <Tab.Panel className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-medium">バトル機能</h3>
              <p className="text-sm text-gray-500">バトル機能の設定を管理します</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${battle.enabled
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
              }`}>
              {battle.enabled ? "有効" : "無効"}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-500">キル報酬</p>
              <p className="font-medium">{battle.points_per_kill.toLocaleString()} {serverData.settings.global_settings.point_unit}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">勝者報酬</p>
              <p className="font-medium">{battle.winner_points.toLocaleString()} {serverData.settings.global_settings.point_unit}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">開始遅延</p>
              <p className="font-medium">{battle.start_delay_minutes}分</p>
            </div>
          </div>
        </Tab.Panel>

        <Tab.Panel className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-medium">ガチャ機能</h3>
              <p className="text-sm text-gray-500">ガチャ機能の設定を管理します</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${gacha.enabled
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
              }`}>
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
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-gray-500">確率: {probability}%</p>
                      </div>
                      <p className="font-medium">{item.points.toLocaleString()} {serverData.settings.global_settings.point_unit}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* メッセージ設定 */}
            <div className="py-6">
              <h4 className="text-base font-medium text-gray-900 mb-4">メッセージ設定</h4>
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">セットアップメッセージ</h5>
                  <p className="text-gray-600">{gacha.messages?.setup || '設定なし'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">デイリーメッセージ</h5>
                  <p className="text-gray-600">{gacha.messages?.daily || '設定なし'}</p>
                  <p className="text-xs text-gray-500 mt-2">変数: {'{user}'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">当選メッセージ</h5>
                  <p className="text-gray-600">{gacha.messages?.win || '設定なし'}</p>
                  <p className="text-xs text-gray-500 mt-2">変数: {'{user}'}, {'{item}'}</p>
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
        </Tab.Panel>

        <Tab.Panel className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-medium">占い機能</h3>
              <p className="text-sm text-gray-500">占い機能の設定を管理します</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${fortune.enabled
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
              }`}>
              {fortune.enabled ? "有効" : "無効"}
            </span>
          </div>
        </Tab.Panel>

        {/* オートメーション設定パネル */}
        <Tab.Panel className="bg-white rounded-xl p-6 shadow-sm">
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium">オートメーション設定</h3>
                <p className="text-sm text-gray-500">自動化ルールの設定を管理します</p>
              </div>
            </div>

            <EditableFeatureCard
              title="ルール設定"
              isEditing={editingSection === 'automation-settings'}
              onEditToggle={() => setEditingSection(
                editingSection === 'automation-settings' ? null : 'automation-settings'
              )}
              onSave={async (data) => {
                setSaving(true);
                try {
                  // // AutomationSettingsFormからのデータ構造を確認
                  // if (!data) {
                  //   console.error('No data received from form');
                  //   return;
                  // }

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
                    history: automationHistory || []
                  }}
                  pointUnit={serverData?.settings?.global_settings?.point_unit}
                  serverId={selectedServerId}
                  serverRoles={serverRoles}
                  serverData={serverData} // serverDataを渡す
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
                        <span className={`px-2 py-1 rounded-full text-sm ${rule.enabled
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                          }`}>
                          {rule.enabled ? "有効" : "無効"}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </EditableFeatureCard>

            {/* 実行履歴の表示 */}
            {Array.isArray(automationHistory) && automationHistory.length > 0 && (
              <div className="mt-8">
                <h4 className="text-lg font-medium mb-4">実行履歴</h4>
                <div className="space-y-4">
                  {automationHistory.map((entry) => (
                    <div key={entry.timestamp} className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{entry.rule_name}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(entry.timestamp).toLocaleString('ja-JP')}
                          </p>
                        </div>
                        <span className={`px-2 py-1 rounded text-sm ${entry.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                          {entry.success ? '成功' : '失敗'}
                        </span>
                      </div>
                      {entry.details && (
                        <p className="text-sm text-gray-600 mt-2">{entry.details}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Tab.Panel>

      </Tab.Panels>
    </Tab.Group>
  </EditableFeatureCard>

  );
};

export default FeatureSettings;
