import React, { useState, useEffect } from 'react';
import { Save, X, AlertCircle } from 'lucide-react';
import { getPointsByUnitId } from '@/utils/gachaHelper';

export const UserPointsForm = ({ 
    user, 
    pointUnit, 
    selectedUnitId, 
    onSave, 
    onCancel 
}) => {
    // 初期値の設定
    const [points, setPoints] = useState(() => {
        const currentPoints = getPointsByUnitId(user.points, selectedUnitId);
        return currentPoints === 0 ? '' : currentPoints.toString();
    });
    
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // ユーザーまたはユニットが変更された場合にポイントを更新
    useEffect(() => {
        const currentPoints = getPointsByUnitId(user.points, selectedUnitId);
        setPoints(currentPoints === 0 ? '' : currentPoints.toString());
    }, [user.points, selectedUnitId]);

    const validatePoints = (value) => {
        if (value === '') return null;
        
        const numValue = Number(value);
        if (isNaN(numValue)) {
            return '無効な値が入力されました';
        }
        if (numValue < 0) {
            return 'ポイントは0以上である必要があります';
        }
        if (!Number.isInteger(numValue)) {
            return 'ポイントは整数である必要があります';
        }
        if (numValue > 999999999) {
            return 'ポイントが大きすぎます';
        }
        return null;
    };

    const handleChange = (e) => {
        const value = e.target.value.trim();
        setPoints(value);
        
        const validationError = validatePoints(value);
        setError(validationError || '');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (error || isSubmitting) return;

        try {
            setIsSubmitting(true);
            const numericPoints = points === '' ? 0 : Number(points);
            await onSave(user.user_id, numericPoints);
        } catch (err) {
            setError('ポイントの更新に失敗しました');
            console.error('Error saving points:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !error) {
            handleSubmit(e);
        } else if (e.key === 'Escape') {
            onCancel();
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full">
            <div className="space-y-3">
                <div className="flex items-center gap-2">
                    <input
                        type="text"
                        pattern="[0-9]*"
                        inputMode="numeric"
                        value={points}
                        onChange={handleChange}
                        onKeyDown={handleKeyDown}
                        className={`w-full px-2 py-1 border rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${
                            error ? 'border-red-500' : ''
                        }`}
                        placeholder="0"
                        disabled={isSubmitting}
                        aria-label={`${pointUnit}を入力`}
                    />
                    <span className="text-sm text-gray-600 whitespace-nowrap">
                        {pointUnit}
                    </span>
                </div>

                {error && (
                    <div className="flex items-center gap-1.5 text-red-600 text-xs">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>{error}</span>
                    </div>
                )}

                <div className="flex justify-end gap-2">
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={isSubmitting}
                        className="px-2 py-1 text-sm rounded text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
                    >
                        <span className="sr-only">キャンセル</span>
                        <X className="w-4 h-4" />
                    </button>
                    <button
                        type="submit"
                        disabled={!!error || isSubmitting}
                        className={`px-2 py-1 text-sm rounded text-green-600 hover:bg-green-50 transition-colors 
                            ${(error || isSubmitting) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <span className="sr-only">保存</span>
                        <Save className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </form>
    );
};