import React, { useState } from 'react';
import { Save, X, AlertCircle } from 'lucide-react';

export const UserPointsForm = ({ user, pointUnit, onSave, onCancel }) => {
  // 数値型として初期値を設定

  console.log('User points raw:', user.points);
  console.log('User points type:', typeof user.points);
  if (typeof user.points === 'object') {
    console.log('User points toString:', user.points.toString());
    console.log('User points valueOf:', user.points.valueOf());
  }

  const [points, setPoints] = useState(() => {
    // Decimalオブジェクト、数値、文字列のいずれの場合も適切に処理
    if (user.points) {
      if (typeof user.points === 'object' && user.points.toString) {
        return Number(user.points.toString());
      }
      return Number(user.points);
    }
    return 0;
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const rawValue = e.target.value; // 入力値の文字列を取得
    const trimmedValue = rawValue.trim(); // トリミングして空白を除去
    const numValue = trimmedValue === '' ? 0 : Number(trimmedValue); // 数値に変換
  
    console.log('Raw input value:', rawValue); // 生の入力値をログ
    console.log('Trimmed input value:', trimmedValue);
    console.log('Parsed number value:', numValue);
  
    if (isNaN(numValue)) {
      setError('無効な値が入力されました');
    } else if (numValue < 0) {
      setError('ポイントは0以上である必要があります');
    } else {
      setError('');
    }
  
    setPoints(trimmedValue); // 入力値をセット（数値ではなく文字列として保持）
  };
  


  const handleSubmit = (e) => {
    e.preventDefault();
    if (error) return;
    onSave(user.user_id, points);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <input
            type="number"
            name="points"
            value={points === 0 ? '' : points} // 初期値やリセット時の空文字対応
            onChange={handleChange}
            min="0"
            className="w-full px-2 py-1 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            placeholder="ポイント"
          />

          <span className="text-sm text-gray-600 whitespace-nowrap">{pointUnit}</span>
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