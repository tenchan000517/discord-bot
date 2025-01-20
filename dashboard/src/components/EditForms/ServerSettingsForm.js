import React, { useState, useEffect } from 'react';
import { validateAndNormalizePointUnits, createNewPointUnitTemplate } from '@/utils/gachaHelper';

export const ServerSettingsForm = ({
  settings,
  onChange,
  onSubmit
}) => {
  // グローバル設定から初期値を設定（point関連は正規化）
  const [formData, setFormData] = useState({
    ...settings.global_settings,
    ...validateAndNormalizePointUnits(settings.global_settings),
    timezone: settings.global_settings.timezone || 'Asia/Tokyo',
    language: settings.global_settings.language || 'ja',
    daily_point_limit: settings.global_settings.daily_point_limit || 0,
    features_enabled: settings.global_settings.features_enabled || {
      gacha: true,
      battle: true,
      fortune: true,
      point_consumption: true
    },
    notifications: {
      points_earned: settings.global_settings.notifications?.points_earned ?? true,
      ranking_updated: settings.global_settings.notifications?.ranking_updated ?? true
    }
  });

  const translateFeatureName = (key) => {
    const translations = {
      gacha: 'ガチャ機能',
      battle: 'バトル機能',
      fortune: '占い機能',
      rewards: 'リワード機能',
      point_consumption: 'ポイント消費'
    };
    return translations[key] || key; // 翻訳がない場合はそのまま表示
  };

  // 設定値が変更された時のハンドラー
  const handleChange = (e) => {
    const { name, value } = e.target;
    const newFormData = {
      ...formData,
      [name]: value,
    };
    setFormData(newFormData);

    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
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

    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  // 機能有効化の切り替えハンドラー
  const handleFeatureToggle = (feature) => {
    const newFormData = {
      ...formData,
      features_enabled: {
        ...formData.features_enabled,
        [feature]: !formData.features_enabled[feature]
      }
    };
    setFormData(newFormData);

    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  // ポイントユニットの更新ハンドラー
  const handlePointUnitChange = (index, key, value) => {
    const updatedPointUnits = formData.point_units.map((unit, i) =>
      i === index ? { ...unit, [key]: value } : unit
    );

    const newFormData = {
      ...formData,
      point_units: updatedPointUnits
    };

    setFormData(newFormData);
    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  // ポイントユニットの追加ハンドラー
  const handleAddPointUnit = () => {
    const newUnit = createNewPointUnitTemplate(formData.point_units);
    const updatedPointUnits = [...formData.point_units, newUnit];

    const newFormData = {
      ...formData,
      point_units: updatedPointUnits
    };

    setFormData(newFormData);
    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  // ポイントユニットの削除ハンドラー
  const handleRemovePointUnit = (index) => {
    const updatedPointUnits = formData.point_units.filter((_, i) => i !== index);

    const newFormData = {
      ...formData,
      point_units: updatedPointUnits
    };

    setFormData(newFormData);
    onChange({
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...newFormData
      }
    });
  };

  const handleSubmit = () => {
    const updatedSettings = {
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...formData
      },
      version: (settings.version || 0) + 1,
      last_modified: new Date().toISOString()
    };

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

      {/* 機能有効化設定 */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">機能有効化設定</h3>
        {Object.entries(formData.features_enabled)
          .filter(([feature]) => !['daily_point_limit', 'notifications'].includes(feature)) // 非表示にするキーをフィルタリング
          .map(([feature, enabled]) => (
            <div key={feature} className="flex items-center justify-between">
              {/* 日本語に翻訳 */}
              <span className="text-sm text-gray-700">
                {translateFeatureName(feature)}
              </span>
              <button
                type="button"
                onClick={() => handleFeatureToggle(feature)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${enabled ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                />
              </button>
            </div>
          ))}
      </div>


      {/* ポイントユニット設定 */}
      {formData.multiple_points_enabled && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">ポイント単位設定</h3>
          {formData.point_units.map((unit, index) => (
            <div key={unit.unit_id} className="grid grid-cols-3 gap-4 items-center">
              <input
                type="text"
                value={unit.name}
                onChange={(e) => handlePointUnitChange(index, 'name', e.target.value)}
                placeholder="ポイント名"
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <input
                type="text"
                value={unit.unit_id}
                onChange={(e) => handlePointUnitChange(index, 'unit_id', e.target.value)}
                placeholder="ユニットID"
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => handleRemovePointUnit(index)}
                className="px-2 py-1 bg-red-500 text-white rounded-md hover:bg-red-600"
              >
                削除
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={handleAddPointUnit}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
          >
            ポイントユニット追加
          </button>
        </div>
      )}

      {/* ポイントユニット設定有効化トグル */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">ポイントユニット設定</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">ポイントユニットを有効にする</span>
          <button
            type="button"
            onClick={() => {
              const newFormData = {
                ...formData,
                multiple_points_enabled: !formData.multiple_points_enabled
              };
              setFormData(newFormData);
              onChange({
                ...settings,
                global_settings: {
                  ...settings.global_settings,
                  ...newFormData
                }
              });
            }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${formData.multiple_points_enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.multiple_points_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
            />
          </button>
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
