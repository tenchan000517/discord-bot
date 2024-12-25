'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSession, signIn } from 'next-auth/react';
import { Alert } from '@/components/ui/Alert';
import { Search, History, Settings, ChevronDown, Trophy, Edit2 } from 'lucide-react';
import CSVImportExport from './EditForms/CSVImportExport';

import RankingList from './ServerDashboard/RankingList'; // 変更
import ServerInfo from './ServerDashboard/ServerInfo'; // 追加
import FeatureSettings from './ServerDashboard/FeatureSettings';

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
  const [changeHistory, setChangeHistory] = useState([]);

  const [automationRules, setAutomationRules] = useState([]);
  const [automationHistory, setAutomationHistory] = useState([]);

  const [serverRoles, setServerRoles] = useState([]);

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
    if (!id || !session) return;

    console.log('[3. Server ID Check] Fetching data for server ID:', id); // ログ追加

    try {
      setLoading(true);
      const [serverResponse, automationResponse, rolesResponse, channelsResponse] = await Promise.all([
        fetch(`/api/servers/${id}`),
        fetch(`/api/servers/${id}/automation`),
        fetch(`/api/servers/${id}/roles`),
        fetch(`/api/servers/${id}/channels`)  // 追加
      ]);

      console.log('[5. Channel Response Check] Channels Response:', await channelsResponse.clone().json()); // ログ追加


      // 認証エラーチェック
      if (serverResponse.status === 401 ||
        automationResponse.status === 401 ||
        rolesResponse.status === 401 ||
        channelsResponse.status === 401) {

        signIn('discord');
        return;
      }

      const serverData = await serverResponse.json();
      const automationData = await automationResponse.json();
      const rolesData = await rolesResponse.json();
      const channelsData = await channelsResponse.json();  // 追加

      // serverDataにチャンネル情報を追加
      serverData.channels = channelsData.channels;

      setServerData(serverData);
      setAutomationRules(automationData.rules);
      setAutomationHistory(automationData.history);
      setServerRoles(rolesData.roles);

      setError(null);
    } catch (err) {
      setError('データの取得に失敗しました');
      console.error('Error fetching server data:', err);

      if (err.message === 'Unauthorized' || err.message === '401: Unauthorized') {
        signIn('discord');
      }
    } finally {
      setLoading(false);
    }
  }, [session]);

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

  const handleUpdateAutomationRule = async (ruleId, updateData) => {
    console.log("[ServerDashboard] handleUpdateAutomationRule called with:", {
      ruleId,
      updateData,
    });
    try {
      console.log('Updating automation rules with:', {
        updateData,
        server_id: selectedServerId
      });

      const payload = {
        ...updateData,
        server_id: selectedServerId,
        ruleId: ruleId || null
      };

      const response = await fetch(`/api/servers/${selectedServerId}/automation`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || 'ルールの更新に失敗しました');
      }

      console.log("[ServerDashboard] Rule update success:", data);

      await fetchServerData(selectedServerId);
      return data;

    } catch (error) {
      console.error('Error updating automation rules:', error);
      setError(error.message);
      throw error;
    }
  };

  useEffect(() => {
    const fetchServers = async () => {
      if (!session) {
        // セッションがない場合は早期リターン
        return;
      }

      try {
        const response = await fetch('/api/servers/list');

        if (response.status === 401) {
          // エラーメッセージを設定
          setError(
            <div className="flex flex-col items-center gap-4">
              <p>セッションの有効期限が切れました。再度ログインしてください。</p>
              <button
                onClick={() => signIn('discord')}
                className="px-6 py-2 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752C4] transition-colors flex items-center gap-2"
              >
                Discordでログイン
              </button>
            </div>
          );
          return;
        }

        const data = await response.json();
        if (data.error) {
          throw new Error(data.error);
        }
        setServers(data.servers);
      } catch (err) {
        if (err.message === 'Unauthorized' || err.message === '401: Unauthorized') {
          setError(
            <div className="flex flex-col items-center gap-4">
              <p>認証に失敗しました。再度ログインしてください。</p>
              <button
                onClick={() => signIn('discord')}
                className="px-6 py-2 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752C4] transition-colors flex items-center gap-2"
              >
                Discordでログイン
              </button>
            </div>
          );
          return;
        }
        setError('サーバー一覧の取得に失敗しました');
        console.error('Error fetching servers:', err);
      }
    };

    if (session) {
      fetchServers();
    }
  }, [session]);

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
              {/* サーバー情報を表示 */}
              <ServerInfo
                serverData={serverData}
                selectedServer={selectedServer}
                editingSection={editingSection}
                setEditingSection={setEditingSection}
                handleUpdateSettings={handleUpdateSettings}
              />

              <FeatureSettings
                serverData={serverData}
                featureData={featureData}
                setFeatureData={setFeatureData}
                editingSection={editingSection}
                setEditingSection={setEditingSection}
                handleUpdateSettings={handleUpdateSettings}
                calculateTotalWeight={calculateTotalWeight}
                automationRules={automationRules}
                automationHistory={automationHistory}
                setAutomationRules={setAutomationRules}
                changeHistory={changeHistory}
                setChangeHistory={setChangeHistory}
                selectedServerId={selectedServerId}
                handleUpdateAutomationRule={handleUpdateAutomationRule}
                setSaving={setSaving}
                setError={setError}
                serverRoles={serverRoles}
              />

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