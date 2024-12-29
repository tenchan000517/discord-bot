import React, { useState } from 'react';
import RankingList from './RankingList';

const RankingListWithPagination = ({ rankings, pointUnit, onUpdatePoints }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50; // 1ページあたりの表示件数

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const totalPages = Math.ceil(rankings.length / itemsPerPage);

  const currentRankings = rankings.slice(startIndex, endIndex);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <div className="space-y-4">
      {/* ランキングリスト */}
      <RankingList
        rankings={currentRankings} // 現在のページのランキングデータ
        pointUnit={pointUnit}
        onUpdatePoints={onUpdatePoints}
      />

      {/* ページネーション */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={handlePrevPage}
          disabled={currentPage === 1}
          className={`px-4 py-2 bg-gray-100 text-gray-700 rounded-lg ${
            currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200'
          }`}
        >
          戻る
        </button>
        <span className="text-sm text-gray-500">
          ページ {currentPage} / {totalPages}
        </span>
        <button
          onClick={handleNextPage}
          disabled={currentPage === totalPages}
          className={`px-4 py-2 bg-gray-100 text-gray-700 rounded-lg ${
            currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200'
          }`}
        >
          次へ
        </button>
      </div>
    </div>
  );
};

export default RankingListWithPagination;
