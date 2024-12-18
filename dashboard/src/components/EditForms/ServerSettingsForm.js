// components/EditForms/ServerSettingsForm.js
import React, { useState } from 'react';

export const ServerSettingsForm = ({ 
  settings, 
  onSubmit 
}) => {
  const [formData, setFormData] = useState({
    point_unit: settings.global_settings.point_unit,
    timezone: settings.global_settings.timezone,
    language: settings.global_settings.language
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    const updatedSettings = {
      ...settings,
      global_settings: {
        ...settings.global_settings,
        ...formData
      },
      version: (settings.version || 0) + 1,
      last_modified: new Date().toISOString()
    };

    await onSubmit(updatedSettings);
  };

  return (
    <div className="space-y-4">
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
      </div>
    </div>
  );
};