// components/EditForms/GachaSettingsForm.js
import React, { useState, useEffect } from 'react';
import { PlusIcon, XIcon } from 'lucide-react';

export const GachaSettingsForm = ({ settings, pointUnit, onChange }) => {
  const [formData, setFormData] = useState({
    enabled: settings.enabled,
    items: [...settings.items]
  });

  const handleChange = (e) => {
    const { name, type, checked } = e.target;
    const newData = {
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(e.target.value, 10) : e.target.value
    };
    setFormData(newData);
    onChange(newData);
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = {
      ...newItems[index],
      [field]: field === 'weight' || field === 'points' ? parseInt(value, 10) : value
    };
    const newData = { ...formData, items: newItems };
    setFormData(newData);
    onChange(newData);
  };

  const addItem = () => {
    const newData = {
      ...formData,
      items: [...formData.items, { name: '', points: 0, weight: 1 }]
    };
    setFormData(newData);
    onChange(newData);
  };

  const removeItem = (index) => {
    const newData = {
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    };
    setFormData(newData);
    onChange(newData);
  };

  // 設定が変更されたときにフォームデータを更新
  useEffect(() => {
    setFormData({
      enabled: settings.enabled,
      items: [...settings.items]
    });
  }, [settings]);

  // ガチャアイテムの合計重みを計算
  const calculateTotalWeight = () => {
    return formData.items.reduce((sum, item) => sum + parseInt(item.weight, 10), 0);
  };

  const calculateProbability = (weight) => {
    const totalWeight = calculateTotalWeight();
    return ((weight / totalWeight) * 100).toFixed(1);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">ガチャ機能</h3>
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

      <div className="space-y-4">
        {formData.items.map((item, index) => (
          <div key={index} className="flex gap-3 items-start">
            <div className="flex-1 grid grid-cols-3 gap-2">
              <div>
                <input
                  type="text"
                  value={item.name}
                  onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                  placeholder="アイテム名"
                  className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={item.points}
                    onChange={(e) => handleItemChange(index, 'points', e.target.value)}
                    placeholder="ポイント"
                    min="0"
                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <span className="text-gray-600 whitespace-nowrap">{pointUnit}</span>
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={item.weight}
                    onChange={(e) => handleItemChange(index, 'weight', e.target.value)}
                    placeholder="重み"
                    min="1"
                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <span className="text-gray-600 whitespace-nowrap">
                    {calculateProbability(item.weight)}%
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => removeItem(index)}
              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <XIcon className="w-5 h-5" />
            </button>
          </div>
        ))}

        <button
          onClick={addItem}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          <span>アイテムを追加</span>
        </button>
      </div>
    </div>
  );
};