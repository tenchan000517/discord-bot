import React, { useState, useMemo, useEffect } from 'react';
import { Edit2 } from 'lucide-react';
import { UserPointsForm } from '../EditForms/UserPointsForm';
import { getPointsByUnitId } from '@/utils/gachaHelper';

const RankingList = ({
    rankings,
    pointUnits,
    selectedUnitId,
    onUpdatePoints
}) => {
    const [editingUserId, setEditingUserId] = useState(null);

    // 現在選択中のポイントユニットを取得
    const currentPointUnit = useMemo(() =>
        pointUnits.find(unit => unit.unit_id === selectedUnitId) || pointUnits[0],
        [pointUnits, selectedUnitId]
    );

    // rankingsをポイントでソート
    const sortedRankings = useMemo(() => {
        return [...rankings]
            .filter(user => {
                // 該当するunit_idのポイントが存在するかを直接チェック
                return user.points && user.points[selectedUnitId] !== undefined;
            })
            .sort((a, b) => {
                const pointsA = a.points[selectedUnitId] || 0;
                const pointsB = b.points[selectedUnitId] || 0;
                return pointsB - pointsA; // 降順にソート
            });
    }, [rankings, selectedUnitId]);


    useEffect(() => {
        console.log('Raw Rankings Data:', rankings);
    }, [rankings]);

    const handleSave = async (userId, newPoints) => {
        try {
            await onUpdatePoints(userId, newPoints, selectedUnitId);
            setEditingUserId(null);
        } catch (error) {
            console.error('Failed to update points:', error);
            // エラー処理は上位コンポーネントで行う
        }
    };

    return (
        <div className="space-y-3">
            {sortedRankings.map((user, index) => (
                editingUserId === user.user_id ? (
                    // 編集モード: 縦に展開
                    <div key={`${user.user_id}-${selectedUnitId}`} className="bg-white p-4 rounded-lg shadow-sm">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-sm font-medium text-gray-500 w-8">#{index + 1}</span>
                            {user.avatar ? (
                                <img
                                    src={`https://cdn.discordapp.com/avatars/${user.user_id}/${user.avatar}.png`}
                                    alt={user.displayName}
                                    className="w-8 h-8 rounded-full"
                                />
                            ) : (
                                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                                    <span className="text-sm font-medium text-gray-600">
                                        {user.displayName?.[0]}
                                    </span>
                                </div>
                            )}
                            <span className="font-medium">{user.displayName}</span>
                        </div>
                        <UserPointsForm
                            user={user}
                            pointUnit={currentPointUnit.name}
                            selectedUnitId={selectedUnitId}
                            onSave={handleSave}
                            onCancel={() => setEditingUserId(null)}
                        />
                    </div>
                ) : (
                    // 通常モード: 1行表示
                    <div key={user.user_id} className="bg-white p-3 rounded-lg shadow-sm">
                        <div className="flex items-center">
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                                <span className="text-sm font-medium text-gray-500 w-8">#{index + 1}</span>
                                {user.avatar ? (
                                    <img
                                        src={`https://cdn.discordapp.com/avatars/${user.user_id}/${user.avatar}.png`}
                                        alt={user.displayName}
                                        className="w-8 h-8 rounded-full flex-shrink-0"
                                    />
                                ) : (
                                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                                        <span className="text-sm font-medium text-gray-600">
                                            {user.displayName?.[0]}
                                        </span>
                                    </div>
                                )}
                                <span className="font-medium truncate">
                                    {user.displayName}
                                </span>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                                <span className="font-medium whitespace-nowrap">
                                    {getPointsByUnitId(user.points, selectedUnitId).toLocaleString()} {currentPointUnit.name}
                                </span>
                                <button
                                    onClick={() => setEditingUserId(user.user_id)}
                                    className="p-1 text-gray-400 hover:text-gray-600"
                                >
                                    <Edit2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                )
            ))}
        </div>
    );
};

export default RankingList;