import React, { useState, useEffect } from 'react';

export const ServerSettingsForm = ({
  settings,
  onChange,
  onSubmit
}) => {
  // グローバル設定から初期値を設定
  const [formData, setFormData] = useState({
    point_unit: settings.global_settings.point_unit || 'pt',
    timezone: settings.global_settings.timezone || 'Asia/Tokyo',
    language: settings.global_settings.language || 'ja',
    daily_point_limit: settings.global_settings.daily_point_limit || 0,
    notifications: {
      points_earned: settings.global_settings.notifications?.points_earned ?? true,
      ranking_updated: settings.global_settings.notifications?.ranking_updated ?? true
    }
  });

  // 設定値が変更された時のハンドラー
  const handleChange = (e) => {
    const { name, value } = e.target;
    const newFormData = {
      ...formData,
      [name]: value,
    };
    setFormData(newFormData);
  
    console.log("handleChange - settings:", settings); // デバッグ用
    console.log("handleChange - newFormData:", newFormData); // デバッグ用
  
    onChange({
      ...settings,
      global_settings: {
        ...newFormData // newFormData だけを展開する
      }
    });
    
  };
  

  // 通知設定の切り替えハンドラー
  const handleNotificationToggle = (key) => {
    const newFormData = {
      ...formData,
      notifications: {
        ...formData.notifications,
        [key]: !formData.notifications[key]
      }
    };
    setFormData(newFormData);

    // 親コンポーネントに変更を通知
    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  const handleSubmit = () => {
    console.log("フォームデータ送信開始:", formData); // ログ追加

    const updatedSettings = {
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...formData
      },
      version: (settings.version || 0) + 1,
      last_modified: new Date().toISOString()
    };

    console.log("送信データ:", updatedSettings); // ログ追加
    onSubmit(updatedSettings);
  };


  return (
    <div className="space-y-6">
      {/* 基本設定 */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">基本設定</h3>
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ポイント単位
            </label>
            <input
              type="text"
              name="point_unit"
              value={formData.point_unit}
              onChange={handleChange}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              タイムゾーン
            </label>
            <select
              name="timezone"
              value={formData.timezone}
              onChange={handleChange}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="Asia/Tokyo">Asia/Tokyo</option>
              <option value="UTC">UTC</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              言語
            </label>
            <select
              name="language"
              value={formData.language}
              onChange={handleChange}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ja">日本語</option>
              <option value="en">English</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              日次ポイント上限
            </label>
            <input
              type="number"
              name="daily_point_limit"
              value={formData.daily_point_limit}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* 通知設定 */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">通知設定</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">ポイント獲得通知</span>
            <button
              type="button"
              onClick={() => handleNotificationToggle('points_earned')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${formData.notifications.points_earned ? 'bg-blue-600' : 'bg-gray-200'
                }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.notifications.points_earned ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">ランキング更新通知</span>
            <button
              type="button"
              onClick={() => handleNotificationToggle('ranking_updated')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${formData.notifications.ranking_updated ? 'bg-blue-600' : 'bg-gray-200'
                }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.notifications.ranking_updated ? 'translate-x-6' : 'translate-x-1'
                  }`}
              />
            </button>
          </div>
        </div>
      </div>
      <button
        type="button"
        onClick={handleSubmit}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        保存
      </button>
    </div>
  );
};