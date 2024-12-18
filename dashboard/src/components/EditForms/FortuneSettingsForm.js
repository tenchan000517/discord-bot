// components/EditForms/FortuneSettingsForm.js
import React, { useState, useEffect } from 'react';

export const FortuneSettingsForm = ({ settings, onChange }) => {
  const [formData, setFormData] = useState({
    enabled: settings.enabled
  });

  const handleChange = (e) => {
    const { name, type, checked } = e.target;
    const newData = {
      ...formData,
      [name]: type === 'checkbox' ? checked : e.target.value
    };
    setFormData(newData);
    onChange(newData);
  };

  // 設定が変更されたときにフォームデータを更新
  useEffect(() => {
    setFormData({
      enabled: settings.enabled
    });
  }, [settings]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">占い機能</h3>
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
    </div>
  );
};