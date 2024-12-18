'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSession, signIn } from 'next-auth/react';
import { EditableFeatureCard } from './EditableFeatureCard';
import { ServerSettingsForm } from './EditForms/ServerSettingsForm';
import { BattleSettingsForm } from './EditForms/BattleSettingsForm';
import { GachaSettingsForm } from './EditForms/GachaSettingsForm';
import { FortuneSettingsForm } from './EditForms/FortuneSettingsForm';
import { UserPointsForm } from './EditForms/UserPointsForm';
import { Alert } from '@/components/ui/Alert';
import { Tab } from '@headlessui/react';
import { Search, History, Settings, ChevronDown, Trophy, Edit2 } from 'lucide-react';
import CSVImportExport from './EditForms/CSVImportExport';

const RankingList = ({ rankings, pointUnit, onUpdatePoints }) => {
  const [editingUserId, setEditingUserId] = useState(null);

  const handleSave = async (userId, newPoints) => {
    await onUpdatePoints(userId, newPoints);
    setEditingUserId(null);
  };

  return (
    <div className="space-y-3">
      {rankings.map((user, index) => (
        editingUserId === user.user_id ? (
          // 編集モード: 縦に展開
          <div key={user.user_id} className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-sm font-medium text-gray-500 w-8">#{index + 1}</span>
              {user.avatar ? (
                <img
                  src={`https://cdn.discordapp.com/avatars/${user.user_id}/${user.avatar}.png`}
                  alt={user.displayName}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">
                    {user.displayName?.[0]}
                  </span>
                </div>
              )}
              <span className="font-medium">{user.displayName}</span>
            </div>
            <UserPointsForm
              user={user}
              onSave={handleSave}
              onCancel={() => setEditingUserId(null)}
              pointUnit={pointUnit}
            />
          </div>
        ) : (
          // 通常モード: 1行表示
          <div key={user.user_id} className="bg-white p-3 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <span className="text-sm font-medium text-gray-500 w-8">#{index + 1}</span>
                {user.avatar ? (
                  <img
                    src={`https://cdn.discordapp.com/avatars/${user.user_id}/${user.avatar}.png`}
                    alt={user.displayName}
                    className="w-8 h-8 rounded-full flex-shrink-0"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium text-gray-600">
                      {user.displayName?.[0]}
                    </span>
                  </div>
                )}
                <span className="font-medium truncate">
                  {user.displayName}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                <span className="font-medium whitespace-nowrap">
                  {(user.points?.total || 0).toLocaleString()} {pointUnit}
                </span>
                <button
                  onClick={() => setEditingUserId(user.user_id)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )
      ))}
    </div>
  );
};

const FeatureSettingsWrapper = ({ settings, pointUnit, onSubmit }) => {
  const [formData, setFormData] = useState({
    battle: settings.feature_settings.battle,
    gacha: settings.feature_settings.gacha,
    fortune: settings.feature_settings.fortune
  });

  useEffect(() => {
    onSubmit({
      ...settings,
      feature_settings: formData
    });
  }, [formData, settings.server_id, settings.global_settings, onSubmit]);

  const handleSettingsChange = (section, newData) => {
    setFormData(prevData => ({
      ...prevData,
      [section]: newData
    }));
  };

  return (
    <div className="space-y-8">
      <BattleSettingsForm
        settings={formData.battle}
        pointUnit={pointUnit}
        onChange={(data) => handleSettingsChange('battle', data)}
      />
      <GachaSettingsForm
        settings={formData.gacha}
        pointUnit={pointUnit}
        onChange={(data) => handleSettingsChange('gacha', data)}
      />
      <FortuneSettingsForm
        settings={formData.fortune}
        onChange={(data) => handleSettingsChange('fortune', data)}
      />
    </div>
  );
};

const ServerDashboard = () => {
  const { data: session, status } = useSession();
  const [servers, setServers] = useState([]);
  const [serverData, setServerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedServerId, setSelectedServerId] = useState('');
  const [editingSection, setEditingSection] = useState(null);
  const [saving, setSaving] = useState(false);
  const [featureData, setFeatureData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [changeHistory, setChangeHistory] = useState([]);
  const [selectedTab, setSelectedTab] = useState(0);

  const selectedServer = useMemo(
    () => servers.find(server => server.id === selectedServerId),
    [servers, selectedServerId]
  );

  const calculateTotalWeight = useMemo(
    () => (items) => items.reduce((sum, item) => sum + parseInt(item.weight, 10), 0),
    []
  );

  useEffect(() => {
    if (serverData?.settings?.feature_settings) {
      setFeatureData(serverData.settings);
    }
  }, [serverData]);

  const handleServerChange = (e) => {
    const serverId = e.target.value;
    setSelectedServerId(serverId);
    setEditingSection(null);
    if (serverId) {
      fetchServerData(serverId);
    } else {
      setServerData(null);
    }
  };

  const fetchServerData = useCallback(async (id) => {
    if (!id) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/servers/${id}`);
      const data = await response.json();

      setServerData(data);
      setError(null);
    } catch (err) {
      setError('データの取得に失敗しました');
      console.error('Error fetching server data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUpdateSettings = useCallback(async (section, data) => {
    setSaving(true);
    try {
      if (!data) {
        throw new Error('更新データが存在しません');
      }

      const response = await fetch(`/api/servers/${selectedServerId}/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          section,
          settings: data
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '設定の更新に失敗しました');
      }

      setChangeHistory(prev => [{
        timestamp: new Date(),
        section,
        changes: data
      }, ...prev]);

      await fetchServerData(selectedServerId);
      setEditingSection(null);
    } catch (err) {
      setError(err.message);
      console.error('Error updating settings:', err);
    } finally {
      setSaving(false);
    }
  }, [selectedServerId, fetchServerData]);

  const handleUpdatePoints = async (userId, newPoints) => {
    try {
      const response = await fetch(`/api/servers/${selectedServerId}/points`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          points: { total: newPoints }
        }),
      });

      if (!response.ok) {
        throw new Error('ポイントの更新に失敗しました');
      }

      await fetchServerData(selectedServerId);
    } catch (error) {
      setError(error.message);
    }
  };

  useEffect(() => {
    const fetchServers = async () => {
      if (!session) return;

      try {
        const response = await fetch('/api/servers/list');
        const data = await response.json();
        if (data.error) {
          throw new Error(data.error);
        }
        setServers(data.servers);
      } catch (err) {
        setError('サーバー一覧の取得に失敗しました');
        console.error('Error fetching servers:', err);
      }
    };

    if (session) {
      fetchServers();
    }
  }, [session]);

  const ServerInfo = useMemo(() => {
    if (!serverData || !selectedServer) return null;

    return (
      <EditableFeatureCard
        title="サーバー情報"
        isEditing={editingSection === 'server-settings'}
        onEditToggle={() => setEditingSection(editingSection === 'server-settings' ? null : 'server-settings')}
        onSave={(data) => handleUpdateSettings('server-settings', data)}
        editForm={
          <ServerSettingsForm
            settings={serverData.settings}
            onSubmit={(data) => handleUpdateSettings('server-settings', data)}
          />
        }
      >
        <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-6 mb-8">
            {selectedServer.icon ? (
              <img
                src={`https://cdn.discordapp.com/icons/${selectedServerId}/${selectedServer.icon}.png`}
                alt="Server Icon"
                className="w-20 h-20 rounded-full ring-2 ring-gray-100"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <span className="text-3xl text-white font-medium">
                  {selectedServer.name.charAt(0)}
                </span>
              </div>
            )}
            <div>
              <h3 className="text-2xl font-bold mb-1">{selectedServer.name}</h3>
              <p className="text-gray-500">ID: {serverData.settings.server_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">ポイント単位</h4>
              <p className="text-lg font-medium">{serverData.settings.global_settings.point_unit}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">タイムゾーン</h4>
              <p className="text-lg font-medium">{serverData.settings.global_settings.timezone}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">言語</h4>
              <p className="text-lg font-medium">{serverData.settings.global_settings.language}</p>
            </div>
          </div>
        </div>
      </EditableFeatureCard>
    );
  }, [serverData, selectedServer, selectedServerId, editingSection, handleUpdateSettings]);

  const FeatureSettings = useMemo(() => {
    if (!serverData?.settings?.feature_settings) return null;

    const { battle, gacha, fortune } = serverData.settings.feature_settings;
    if (!battle || !gacha || !fortune) return null;

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
          </Tab.Panels>
        </Tab.Group>
      </EditableFeatureCard>
    );
  }, [serverData, calculateTotalWeight, editingSection, featureData, handleUpdateSettings]);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">読み込み中...</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <button
          onClick={() => signIn('discord')}
          className="px-6 py-2 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752C4] transition-colors"
        >
          Discordでログイン
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-8">サーバーダッシュボード</h1>

        <div className="mb-8">
          <select
            value={selectedServerId}
            onChange={handleServerChange}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="">サーバーを選択してください</option>
            {servers.map(server => (
              <option key={server.id} value={server.id}>
                {server.name}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-8">
            <p>{error}</p>
          </Alert>
        )}

        {serverData && selectedServer && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              {ServerInfo}
              {FeatureSettings}

              {changeHistory.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <History className="w-5 h-5 text-gray-400" />
                    <h3 className="text-lg font-medium">変更履歴</h3>
                  </div>
                  <div className="space-y-4">
                    {changeHistory.map((change, index) => (
                      <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium">
                            {change.section === 'server-settings' ? 'サーバー設定'
                              : change.section === 'feature-settings' ? '機能設定'
                                : change.section}
                            の変更
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(change.timestamp).toLocaleString('ja-JP')}
                          </p>
                        </div>
                        <button
                          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          詳細を表示
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-1">
              <div className="space-y-4">
                <CSVImportExport
                  serverId={selectedServerId}
                  onUpdateComplete={() => fetchServerData(selectedServerId)}
                />
                <div className="bg-white rounded-lg shadow-sm">
                  <div className="p-4 border-b">
                    <div className="flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-yellow-500" />
                      <h3 className="text-lg font-medium">ポイントランキング</h3>
                    </div>
                  </div>
                  <div className="p-4">
                    <RankingList
                      rankings={serverData.rankings}
                      pointUnit={serverData.settings.global_settings.point_unit}
                      onUpdatePoints={handleUpdatePoints}
                    />
                  </div>
                </div>

              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServerDashboard;