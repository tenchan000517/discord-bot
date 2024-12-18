// components/EditForms/BattleSettingsForm.js
import React, { useState, useEffect } from 'react';

export const BattleSettingsForm = ({ settings, pointUnit, onChange }) => {
  const [formData, setFormData] = useState({
    enabled: settings.enabled,
    points_per_kill: settings.points_per_kill,
    winner_points: settings.winner_points,
    start_delay_minutes: settings.start_delay_minutes
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newData = {
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value, 10) : value
    };
    setFormData(newData);
    onChange(newData);
  };

  // 設定が変更されたときにフォームデータを更新
  useEffect(() => {
    setFormData({
      enabled: settings.enabled,
      points_per_kill: settings.points_per_kill,
      winner_points: settings.winner_points,
      start_delay_minutes: settings.start_delay_minutes
    });
  }, [settings]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">バトル機能</h3>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            name="enabled"
            checked={formData.enabled}
            onChange={handleChange}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            キル報酬
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              name="points_per_kill"
              value={formData.points_per_kill}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <span className="text-gray-600">{pointUnit}</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            勝者報酬
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              name="winner_points"
              value={formData.winner_points}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <span className="text-gray-600">{pointUnit}</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            開始遅延（分）
          </label>
          <input
            type="number"
            name="start_delay_minutes"
            value={formData.start_delay_minutes}
            onChange={handleChange}
            min="0"
            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
};