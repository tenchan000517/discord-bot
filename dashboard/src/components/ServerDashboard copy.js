'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSession, signIn } from 'next-auth/react';
import { Alert } from '@/components/ui/Alert';
import {
  BarChart3,
  Users,
  Settings,
  Swords,
  Gift,
  Stars,
  Award,
  Workflow,
  Database,
  Trophy,
  Bell,
  Menu,
  Coins,
  History,
  Search
} from 'lucide-react';
import CSVImportExport from './EditForms/CSVImportExport';
import RankingList from './ServerDashboard/RankingList';
import ServerInfo from './ServerDashboard/ServerInfo';
import FeatureSettings from './ServerDashboard/FeatureSettings';
// import ServerSettings from './ServerDashboard/ServerSettings';
import MobileMenu from './MobileMenu';

// ポイントデータを正規化するヘルパー関数
const normalizePoints = (points) => {
  if (typeof points === 'number' || typeof points === 'string') {
    return Number(points);
  }
  if (points && typeof points === 'object') {
    return Number(points.total || 0);
  }
  return 0;
};

// メニュー構成の定義
const menuItems = [
  {
    category: 'アナリティクス',
    items: [
      { id: 'dashboard', label: 'ダッシュボード', icon: BarChart3 },
      { id: 'user-analysis', label: 'ユーザー分析', icon: Users }
    ]
  },
  {
    category: '設定',
    items: [
      { id: 'server-settings', label: '基本設定', icon: Settings },
      { id: 'battle', label: 'バトル設定', icon: Swords },
      { id: 'gacha', label: 'ガチャ設定', icon: Gift },
      { id: 'fortune', label: '占い設定', icon: Stars },
      { id: 'rewards', label: '報酬設定', icon: Award },
      { id: 'point-consumption', label: 'ポイント消費設定', icon: Coins },
      { id: 'automation', label: 'オートメーション', icon: Workflow }
    ]
  },
  {
    category: 'データ管理',
    items: [
      { id: 'import-export', label: 'インポート/エクスポート', icon: Database }
    ]
  }
];

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
  const [serverSettings, setServerSettings] = useState(null);
  const [changeHistory, setChangeHistory] = useState([]);
  const [automationRules, setAutomationRules] = useState([]);
  const [serverRoles, setServerRoles] = useState([]);
  const [selectedMenu, setSelectedMenu] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
      setServerSettings(serverData.settings.global_settings);
    }
  }, [serverData]);

  const handleServerChange = (e) => {
    const serverId = e.target.value;
    setSelectedServerId(serverId);
    setEditingSection(null);
    setSelectedMenu('dashboard');
    if (serverId) {
      fetchServerData(serverId);
    } else {
      setServerData(null);
      setServerSettings(null);
    }
  };

  const fetchServerData = useCallback(async (id) => {
    if (!id || !session) return;
    try {
      setLoading(true);
      const [serverResponse, automationResponse, rolesResponse, channelsResponse] = await Promise.all([
        fetch(`/api/servers/${id}`),
        fetch(`/api/servers/${id}/automation`),
        fetch(`/api/servers/${id}/roles`),
        fetch(`/api/servers/${id}/channels`)
      ]);

      if (serverResponse.status === 401 || automationResponse.status === 401 ||
        rolesResponse.status === 401 || channelsResponse.status === 401) {
        signIn('discord');
        return;
      }

      const serverData = await serverResponse.json();
      const automationData = await automationResponse.json();
      const rolesData = await rolesResponse.json();
      const channelsData = await channelsResponse.json();

      serverData.channels = channelsData.channels;

      setServerData(serverData);
      setAutomationRules(automationData.rules);
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
    console.log('handleUpdateSettings - section:', section);
    console.log('handleUpdateSettings - data:', data); // データ確認

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

      // デバッグログを追加
      console.log('handleUpdateSettings - Fetch Request Body:', {
        section,
        settings: data,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '設定の更新に失敗しました');
      }

      // 変更履歴の更新
      setChangeHistory(prev => [{
        timestamp: new Date(),
        section,
        changes: data
      }, ...prev]);

      // サーバーデータの再取得
      await fetchServerData(selectedServerId);
      setEditingSection(null);
    } catch (err) {
      setError(err.message);
      console.error('Error updating settings:', err);
    } finally {
      setSaving(false);
    }
  }, [selectedServerId, fetchServerData]);

  // ポイント更新のハンドラー
  const handleUpdatePoints = async (userId, newPoints) => {
    try {
      const aws = new AWSWrapper();
      await aws.updateUserPoints(selectedServerId, userId, newPoints);
      await fetchServerData(selectedServerId); // 更新後にデータを再取得
    } catch (error) {
      setError('ポイントの更新に失敗しました');
      console.error('Error updating points:', error);
    }
  };

  const handleUpdateAutomationRule = async (ruleId, updateData) => {
    try {
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

      await fetchServerData(selectedServerId);
      return data;
    } catch (error) {
      console.error('Error updating automation rules:', error);
      setError(error.message);
      throw error;
    }
  };

  // サーバー一覧の取得
  useEffect(() => {
    const fetchServers = async () => {
      if (!session) return;

      try {
        const response = await fetch('/api/servers/list');

        if (response.status === 401) {
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

  // ローディング状態のUI
  if (status === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="p-8 bg-white rounded-lg shadow-sm">
          <div className="flex flex-col items-center gap-4">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <div className="text-lg font-medium text-gray-600">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  // 未ログイン状態のUI
  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="p-8 bg-white rounded-lg shadow-sm">
          <button
            onClick={() => signIn('discord')}
            className="px-6 py-3 bg-[#5865F2] text-white rounded-lg hover:bg-[#4752C4] 
                     transition-colors flex items-center gap-3 min-w-[200px] justify-center"
          >
            <img src="/icon_clyde_white_RGB.png" alt="" className="w-6 h-6" />
            Discordでログイン
          </button>
        </div>
      </div>
    );
  }

  // 2. 設定関連のレンダリングを分離
  const renderSettingsSection = () => {
    return (
      <div className="bg-white rounded-lg shadow-sm">
        <FeatureSettings
          serverData={serverData}
          featureData={featureData}
          setFeatureData={setFeatureData}
          editingSection={editingSection}
          setEditingSection={setEditingSection}
          handleUpdateSettings={handleUpdateSettings}
          calculateTotalWeight={calculateTotalWeight}
          automationRules={automationRules}
          setAutomationRules={setAutomationRules}
          changeHistory={changeHistory}
          setChangeHistory={setChangeHistory}
          selectedServerId={selectedServerId}
          selectedServer={selectedServer}
          handleUpdateAutomationRule={handleUpdateAutomationRule}
          setSaving={setSaving}
          setError={setError}
          serverRoles={serverRoles}
          selectedMenu={selectedMenu}
          setServerData={setServerData}
        />
      </div>
    );
  };

  const renderContent = () => {
    if (!serverData || !selectedServer) return null;

    switch (selectedMenu) {
      case 'dashboard':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-medium mb-4">ユーザー統計</h3>
                <div className="text-3xl font-bold">{serverData.rankings.length}</div>
                <p className="text-gray-500">総ユーザー数</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-medium mb-4">累計ポイント</h3>
                <div className="text-3xl font-bold">
                  {serverData.rankings
                    .reduce((sum, user) => sum + user.points, 0)
                    .toLocaleString()}
                </div>
                <p className="text-gray-500">
                  {serverData.settings?.global_settings?.point_unit || 'ポイント'}
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-medium mb-4">アクティブ率</h3>
                <div className="text-3xl font-bold">
                  {((serverData.rankings.filter(user => user.lastActive &&
                    new Date(user.lastActive) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length
                    / serverData.rankings.length) * 100).toFixed(1)}%
                </div>
                <p className="text-gray-500">過去7日間</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* メインコンテンツエリア */}
              <div className="lg:col-span-2 space-y-8">
                {/* サーバー情報 */}
                <div className="bg-white rounded-lg shadow-sm">
                  <ServerInfo
                    serverData={serverData}
                    selectedServer={selectedServer}
                    editingSection={editingSection}
                    setEditingSection={setEditingSection}
                    handleUpdateSettings={handleUpdateSettings}
                  />
                </div>

                {/* 変更履歴 */}
                {changeHistory.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6">
                      <History className="w-5 h-5 text-gray-400" />
                      <h3 className="text-lg font-medium">変更履歴</h3>
                    </div>
                    <div className="space-y-4">
                      {changeHistory.slice(0, 5).map((change, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                        >
                          <div>
                            <p className="font-medium">
                              {change.section === 'server-settings' ? 'サーバー設定'
                                : change.section === 'feature-settings' ? '機能設定'
                                  : change.section === 'automation' ? 'オートメーション'
                                    : change.section}
                              の変更
                            </p>
                            <p className="text-sm text-gray-500">
                              {new Date(change.timestamp).toLocaleString('ja-JP')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* サイドバー */}
              <div className="space-y-8">
                {/* ランキング */}
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
        );

      case 'server-settings':
      case 'battle':
      case 'gacha':
      case 'fortune':
      case 'rewards':
      case 'point-consumption': // ポイント消費設定を追加
      case 'automation':
        return renderSettingsSection();

      case 'import-export':
        return (
          <div className="bg-white rounded-lg shadow-sm">
            <CSVImportExport
              serverId={selectedServerId}
              onUpdateComplete={() => fetchServerData(selectedServerId)}
            />
          </div>
        );

      default:
        return (
          <div className="text-center py-12">
            <p className="text-gray-500">準備中の機能です</p>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm">
        <div className="w-full max-w-full mx-auto px-4 sm:px-6 py-4">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-4 lg:gap-6">
            {/* サーバー選択フィールド
            <select
              value={selectedServerId}
              onChange={handleServerChange}
              className="w-80 sm:w-80 lg:w-96 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value="">サーバーを選択してください</option>
              {servers.map(server => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </select> */}

            <div className="flex flex-col lg:flex-row items-stretch lg:items-center lg:justify-between gap-4 lg:gap-6">
              {/* ボタン類 */}
              <div className="flex justify-end items-center gap-4 w-full lg:w-auto order-1 lg:order-none">
                <a
                  href="https://discord.com/oauth2/authorize?client_id=1313859672826052679&permissions=268823616&integration_type=0&scope=bot+applications.commands"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-[#5865F2] hover:bg-[#4752C4] text-white rounded-lg transition-colors"
                >
                  <img src="/icon_clyde_white_RGB.png" alt="" className="w-6 h-5" />
                  ボットを招待
                </a>

                <button
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  aria-label="通知"
                >
                  <Bell className="w-5 h-5" />
                </button>

                {/* ハンバーガーメニューボタン */}
                <button
                  onClick={() => setIsMobileMenuOpen(true)}
                  className="lg:hidden p-2 hover:bg-gray-100 rounded-full transition-colors"
                  aria-label="メニューを開く"
                >
                  <Menu className="w-5 h-5" />
                </button>
              </div>

              {/* サーバー選択フィールド */}
              <select
                value={selectedServerId}
                onChange={handleServerChange}
                className="w-full max-w-full sm:max-w-md lg:w-96 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none order-2 lg:order-none"
              >
                <option value="">サーバーを選択してください</option>
                {servers.map(server => (
                  <option key={server.id} value={server.id}>
                    {server.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

        </div>
      </header >

      {/* メインコンテンツ */}
      <div className="w-full max-w-full mx-auto px-4 sm:px-6 py-4">
        {error && (
          <Alert variant="destructive" className="mb-8">
            <p>{error}</p>
          </Alert>
        )}

        {selectedServerId ? (
          <div className="flex gap-8">
            {/* PCサイドメニュー */}
            <div className="hidden lg:block w-64 flex-shrink-0">
              <div className="bg-white rounded-lg shadow-sm">
                <nav className="p-2">
                  {menuItems.map((group) => (
                    <div key={group.category} className="mb-4">
                      <div className="px-4 py-2 text-sm font-medium text-gray-500">
                        {group.category}
                      </div>
                      {group.items.map((item) => {
                        const Icon = item.icon;
                        return (
                          <button
                            key={item.id}
                            onClick={() => {
                              setSelectedMenu(item.id);
                              setEditingSection(null);
                            }}
                            className={`w-full flex items-center px-4 py-3 rounded-lg text-left transition-colors 
                        ${selectedMenu === item.id ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                          >
                            <Icon className="w-5 h-5 mr-3" />
                            {item.label}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </nav>
              </div>
            </div>

            {/* モバイルメニュー */}
            <MobileMenu
              isOpen={isMobileMenuOpen}
              onClose={() => setIsMobileMenuOpen(false)}
              menuItems={menuItems}
              selectedMenu={selectedMenu}
              setSelectedMenu={setSelectedMenu}
            />

            {/* メインコンテンツエリア */}
            <div className="flex-1">
              {renderContent()}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">サーバーを選択してください</p>
          </div>
        )
        }
      </div >
    </div >
  );
};

export default ServerDashboard;