import React, { useState } from 'react';
import { Save, X, AlertCircle } from 'lucide-react';

export const UserPointsForm = ({ user, pointUnit, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    total: user.points?.total || 0,
    gacha: user.points?.gacha || 0,
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numValue = parseInt(value, 10);
    
    setFormData(prev => ({
      ...prev,
      [name]: isNaN(numValue) ? 0 : numValue
    }));

    if (name === 'gacha' && numValue > formData.total) {
      setError('ガチャポイントは総ポイントを超えることはできません');
    } else if (name === 'total' && numValue < formData.gacha) {
      setError('総ポイントはガチャポイントより小さくすることはできません');
    } else {
      setError('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (error) return;

    const updatedPoints = {
      ...user.points,
      total: formData.total,
      gacha: formData.gacha,
      version: (user.points?.version || 0) + 1
    };

    onSave(user.user_id, updatedPoints);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                name="total"
                value={formData.total}
                onChange={handleChange}
                min="0"
                className="w-full px-2 py-1 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="総ポイント"
              />
              <span className="text-sm text-gray-600 whitespace-nowrap">{pointUnit}</span>
            </div>
            <label className="block text-xs text-gray-500 mt-1">
              総ポイント
            </label>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                name="gacha"
                value={formData.gacha}
                onChange={handleChange}
                min="0"
                className="w-full px-2 py-1 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="ガチャポイント"
              />
              <span className="text-sm text-gray-600 whitespace-nowrap">{pointUnit}</span>
            </div>
            <label className="block text-xs text-gray-500 mt-1">
              ガチャポイント
            </label>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-1.5 text-red-600 text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end gap-2 mt-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-2 py-1 text-sm rounded text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <span className="sr-only">キャンセル</span>
            <X className="w-4 h-4" />
          </button>
          <button
            type="submit"
            disabled={!!error}
            className="px-2 py-1 text-sm rounded text-green-600 hover:bg-green-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="sr-only">保存</span>
            <Save className="w-4 h-4" />
          </button>
        </div>
      </div>
    </form>
  );
};