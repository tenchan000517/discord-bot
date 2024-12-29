// src/components/EditForms/RewardsSettingsForm.js
'use client';

import React, { useState, useEffect } from 'react';
import { Alert } from '@/components/ui/Alert';

const RewardsSettingsForm = ({ settings, onUpdate, serverRoles }) => {
  const [web3Settings, setWeb3Settings] = useState({
    rpc_url: '',
    nft_contract_address: '',
    token_contract_address: '',
    private_key: ''
  });

  const [couponApiSettings, setCouponApiSettings] = useState({
    api_url: '',
    api_key: ''
  });

  const [limitSettings, setLimitSettings] = useState({
    min_points_coupon: 0,
    max_points_coupon: 0,
    min_points_nft: 0,
    min_points_token: 0,
    token_conversion_rate: 0.1
  });

  const [error, setError] = useState(null);

  useEffect(() => {
    if (settings?.rewards) {
      const { web3, coupon_api, limits } = settings.rewards;
      if (web3) setWeb3Settings(web3);
      if (coupon_api) setCouponApiSettings(coupon_api);
      if (limits) setLimitSettings(limits);
    }
  }, [settings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const updatedSettings = {
        ...settings,
        rewards: {
          enabled: true,
          web3: web3Settings,
          coupon_api: couponApiSettings,
          limits: limitSettings
        }
      };

      await onUpdate(updatedSettings);
    } catch (err) {
      setError('設定の更新に失敗しました');
      console.error(err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <p>{error}</p>
        </Alert>
      )}

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Web3設定</h3>
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">RPC URL</label>
            <input
              type="text"
              value={web3Settings.rpc_url}
              onChange={(e) => setWeb3Settings({ ...web3Settings, rpc_url: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="https://example.rpc.url"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">NFTコントラクトアドレス</label>
            <input
              type="text"
              value={web3Settings.nft_contract_address}
              onChange={(e) => setWeb3Settings({ ...web3Settings, nft_contract_address: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="0x..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">トークンコントラクトアドレス</label>
            <input
              type="text"
              value={web3Settings.token_contract_address}
              onChange={(e) => setWeb3Settings({ ...web3Settings, token_contract_address: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="0x..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">プライベートキー</label>
            <input
              type="password"
              value={web3Settings.private_key}
              onChange={(e) => setWeb3Settings({ ...web3Settings, private_key: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="秘密鍵を入力"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">クーポンAPI設定</h3>
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">API URL</label>
            <input
              type="text"
              value={couponApiSettings.api_url}
              onChange={(e) => setCouponApiSettings({ ...couponApiSettings, api_url: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="https://api.example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">APIキー</label>
            <input
              type="password"
              value={couponApiSettings.api_key}
              onChange={(e) => setCouponApiSettings({ ...couponApiSettings, api_key: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="APIキーを入力"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">制限値設定</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">クーポン交換最小ポイント</label>
            <input
              type="number"
              value={limitSettings.min_points_coupon}
              onChange={(e) => setLimitSettings({ ...limitSettings, min_points_coupon: parseInt(e.target.value) })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">クーポン交換最大ポイント</label>
            <input
              type="number"
              value={limitSettings.max_points_coupon}
              onChange={(e) => setLimitSettings({ ...limitSettings, max_points_coupon: parseInt(e.target.value) })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">NFT発行最小ポイント</label>
            <input
              type="number"
              value={limitSettings.min_points_nft}
              onChange={(e) => setLimitSettings({ ...limitSettings, min_points_nft: parseInt(e.target.value) })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">トークン交換最小ポイント</label>
            <input
              type="number"
              value={limitSettings.min_points_token}
              onChange={(e) => setLimitSettings({ ...limitSettings, min_points_token: parseInt(e.target.value) })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">トークン変換レート</label>
            <input
              type="number"
              value={limitSettings.token_conversion_rate}
              onChange={(e) => setLimitSettings({ ...limitSettings, token_conversion_rate: parseFloat(e.target.value) })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              min="0"
              max="1"
              step="0.01"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-4">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          保存
        </button>
      </div>
    </form>
  );
};

export { RewardsSettingsForm };
export default RewardsSettingsForm;