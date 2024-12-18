import React, { useState } from 'react';
import { Upload, Download, AlertCircle } from 'lucide-react';
import Papa from 'papaparse';

const CSVImportExport = ({ serverId, onUpdateComplete }) => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/servers/${serverId}`);
      if (!response.ok) throw new Error('Export failed');
      
      const data = await response.json();
      
      // Convert user data to CSV format
      const csvData = data.rankings.map(user => ({
        user_id: user.user_id,
        display_name: user.displayName,
        total_points: user.points?.total || 0,
        gacha_points: user.points?.gacha || 0
      }));

      // Configure CSV options
      const csv = Papa.unparse(csvData, {
        quotes: false,
        delimiter: ',',
        header: true,
        transform: (value) => {
          if (typeof value === 'number') {
            return value.toString();
          }
          return value;
        }
      });

      // Create and download file
      const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csv], { type: 'text/csv;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `points_${serverId}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError('エクスポートに失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setLoading(true);
      
      // Parse CSV
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        transform: (value, field) => {
          if (field === 'user_id') {
            return value.toString();
          }
          if (field === 'total_points' || field === 'gacha_points') {
            return parseInt(value, 10) || 0;
          }
          return value;
        },
        complete: async (results) => {
          try {
            // 各ユーザーのポイントを更新
            for (const row of results.data) {
              await fetch(`/api/servers/${serverId}/points`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  user_id: row.user_id,
                  points: {
                    total: parseInt(row.total_points, 10) || 0,
                    gacha: parseInt(row.gacha_points, 10) || 0
                  }
                }),
              });
            }
            
            onUpdateComplete?.();
          } catch (err) {
            setError('インポートに失敗しました');
            console.error(err);
          } finally {
            setLoading(false);
          }
        },
        error: (err) => {
          setError('CSVの解析に失敗しました');
          console.error(err);
          setLoading(false);
        }
      });
    } catch (err) {
      setError('ファイルの読み込みに失敗しました');
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-medium mb-4">ポイントデータの管理</h3>
      
      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm mb-4">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
      
      <div className="flex gap-4">
        <button
          onClick={handleExport}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          CSVエクスポート
        </button>
        
        <label className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors cursor-pointer disabled:opacity-50">
          <Upload className="w-4 h-4" />
          CSVインポート
          <input
            type="file"
            accept=".csv"
            onChange={handleImport}
            disabled={loading}
            className="hidden"
          />
        </label>
      </div>
    </div>
  );
};

export default CSVImportExport;