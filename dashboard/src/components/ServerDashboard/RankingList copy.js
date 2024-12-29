'use client';

import React, { useState } from 'react';
import { Edit2 } from 'lucide-react';
import { UserPointsForm } from '../EditForms/UserPointsForm';

// ポイント正規化関数
const normalizePoints = (points) => {
    if (typeof points === 'number' || typeof points === 'string') {
        return Number(points);
    }
    if (points && typeof points === 'object') {
        return Number(points.total || 0);
    }
    return 0;
};

const RankingList = ({ rankings, pointUnit, onUpdatePoints }) => {
    const [editingUserId, setEditingUserId] = useState(null);

    const handleSave = async (userId, newPoints) => {
        await onUpdatePoints(userId, newPoints);
        setEditingUserId(null);
    };

    // rankingsをポイントでソート
    const sortedRankings = [...rankings].sort((a, b) =>
        normalizePoints(b.points) - normalizePoints(a.points)
    );

    return (
        <div className="space-y-3">
            {sortedRankings.map((user, index) => (
                editingUserId === user.user_id ? (
                    // 編集モード: 縦に展開
                    <div key={user.user_id} className="bg-white p-4 rounded-lg shadow-sm">
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
                            user={user}  // 正規化せずに生のデータを渡す

                            onSave={handleSave}
                            onCancel={() => setEditingUserId(null)}
                            pointUnit={pointUnit}
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
                                    {normalizePoints(user.points).toLocaleString()} {pointUnit}
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