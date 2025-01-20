import React, { useState, useEffect, useMemo } from 'react';
import { Search } from 'lucide-react';
import RankingList from './RankingList';
import { getPointsByUnitId } from '@/utils/gachaHelper';

const RankingListWithPagination = ({
  rankings = [],
  globalSettings = {
    multiple_points_enabled: false,
    point_units: [{ unit_id: "1", name: "ポイント" }]
  },
  onUpdatePoints
}) => {
  const defaultUnitId = globalSettings?.point_units?.[0]?.unit_id ?? "1";
  
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUnitId, setSelectedUnitId] = useState(defaultUnitId);
  
  const itemsPerPage = 50;

  const pointUnits = useMemo(() =>
    globalSettings?.point_units ?? [{ unit_id: "1", name: "ポイント" }]
  , [globalSettings?.point_units]);

  // フィルタリングとソート処理
  const filteredAndSortedRankings = useMemo(() => {
    // 検索クエリとunit_idによるフィルタリング
    return rankings
      .filter(user => {
        const matchesSearch = !searchQuery || 
          user.displayName?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesUnitId = user.unit_id === selectedUnitId;
        return matchesSearch && matchesUnitId;
      })
      .sort((a, b) => {
        const pointsA = getPointsByUnitId(a.points, selectedUnitId) || 0;
        const pointsB = getPointsByUnitId(b.points, selectedUnitId) || 0;
        return pointsB - pointsA;
      });
  }, [rankings, searchQuery, selectedUnitId]);

  // ページネーション処理
  const paginatedRankings = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedRankings.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAndSortedRankings, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredAndSortedRankings.length / itemsPerPage);

  // ページが範囲外になった場合に修正
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(Math.max(1, totalPages));
    }
  }, [totalPages, currentPage]);

  // 検索ハンドラー
  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  // unit_id変更ハンドラー
  const handleUnitIdChange = (unitId) => {
    setSelectedUnitId(unitId);
    setCurrentPage(1);
  };

  // ページ変更ハンドラー
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  // ポイント更新ハンドラー
  const handlePointUpdate = async (userId, newPoints) => {
    if (onUpdatePoints) {
      try {
        await onUpdatePoints(userId, newPoints, selectedUnitId);
        console.log(`Points updated for user ${userId} to ${newPoints} in unit ${selectedUnitId}`);
      } catch (error) {
        console.error('Failed to update points:', error);
      }
    }
  };

  return (
    <div className="space-y-4">
      {/* ポイントプール選択 */}
      {globalSettings?.multiple_points_enabled && (
        <div className="flex items-center gap-2">
          <label htmlFor="pointUnit" className="text-sm text-gray-600">
            ポイントプール:
          </label>
          <select
            id="pointUnit"
            value={selectedUnitId}
            onChange={(e) => handleUnitIdChange(e.target.value)}
            className="px-3 py-1.5 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            {pointUnits.map(unit => (
              <option key={unit.unit_id} value={unit.unit_id}>
                {unit.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 検索バー */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={handleSearch}
          placeholder="ユーザー名で検索..."
          className="w-full pl-9 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
      </div>

      {/* 検索結果が0件の場合のメッセージ */}
      {filteredAndSortedRankings.length === 0 ? (
        <div className="text-center py-4 text-gray-500">
          検索結果が見つかりませんでした
        </div>
      ) : (
        <>
          {/* ランキングリスト */}
          <RankingList
            rankings={paginatedRankings}
            pointUnits={pointUnits}
            selectedUnitId={selectedUnitId}
            onUpdatePoints={handlePointUpdate}
          />

          {/* ページネーション */}
          <div className="flex justify-between items-center mt-4">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className={`px-4 py-2 bg-gray-100 text-gray-700 rounded-lg ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200'
                }`}
            >
              戻る
            </button>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {filteredAndSortedRankings.length}件中
                {(currentPage - 1) * itemsPerPage + 1}-
                {Math.min(currentPage * itemsPerPage, filteredAndSortedRankings.length)}件を表示
              </span>
              <select
                value={currentPage}
                onChange={(e) => handlePageChange(Number(e.target.value))}
                className="px-2 py-1 border rounded text-sm"
              >
                {[...Array(totalPages)].map((_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {i + 1} / {totalPages}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={`px-4 py-2 bg-gray-100 text-gray-700 rounded-lg ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200'
                }`}
            >
              次へ
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default RankingListWithPagination;