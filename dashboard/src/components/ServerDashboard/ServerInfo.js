import React from 'react';
import { EditableFeatureCard } from '../EditableFeatureCard';
import { ServerSettingsForm } from '../EditForms/ServerSettingsForm';
import { validateAndNormalizePointUnits  } from '@/utils/gachaHelper';

const ServerInfo = ({
  serverData,
  selectedServer,
  editingSection,
  setEditingSection,
  handleUpdateSettings,
  featureSettings,
}) => {
  if (!serverData || !selectedServer) return null;

  // グローバル設定の正規化
  const globalSettings = {
    ...serverData?.settings?.global_settings ?? {
      timezone: '未設定',
      language: '未設定'
    },
    // ヘルパー関数で point_unit と point_units を一括で正規化
    ...validateAndNormalizePointUnits(serverData?.settings?.global_settings)
  };

  const getLinkedFeatures = (pointUnitId, featureSettings) => {
    const features = [];

    if (featureSettings?.gacha?.gacha_list) {
      const linkedGacha = featureSettings.gacha.gacha_list.filter(
        (gacha) => gacha.point_unit_id === pointUnitId
      );
      if (linkedGacha.length > 0) {
        features.push({
          type: 'gacha',
          name: 'ガチャ',
          details: linkedGacha.map((gacha) => gacha.name),
          enabled: featureSettings.gacha.enabled,
        });
      }
    }

    return features;
  };

    // フォームの変更を処理するハンドラー
    const handleFormChange = (newSettings) => {
      // 一時的な変更として扱う（保存ボタンを押すまで確定しない）
      console.log('Form changed:', newSettings);
    };

  return (
    <EditableFeatureCard
      title="サーバー情報"
      isEditing={editingSection === 'server-settings'}
      onEditToggle={() =>
        setEditingSection(
          editingSection === 'server-settings' ? null : 'server-settings'
        )
      }
      onSave={(data) => handleUpdateSettings('server-settings', data)}
      editForm={
        <ServerSettingsForm
          settings={serverData.settings}
          onChange={handleFormChange}  // onChange handler を追加
          onSubmit={(data) => handleUpdateSettings('server-settings', data)}
        />
      }
    >
      <div className="bg-white rounded-lg shadow-sm p-2 md:p-6 hover:shadow-md transition-shadow">
        <div className="flex flex-col md:flex-row items-center gap-4 md:gap-6 mb-6 md:mb-8">
          {selectedServer.icon ? (
            <img
              src={`https://cdn.discordapp.com/icons/${serverData.settings.server_id}/${selectedServer.icon}.png`}
              alt="Server Icon"
              className="w-16 h-16 md:w-20 md:h-20 rounded-full ring-2 ring-gray-100"
            />
          ) : (
            <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <span className="text-2xl md:text-3xl text-white font-medium">
                {selectedServer.name.charAt(0)}
              </span>
            </div>
          )}
          <div className="text-center md:text-left">
            <h3 className="text-xl md:text-2xl font-bold mb-1">
              {selectedServer.name}
            </h3>
            <p className="text-sm md:text-base text-gray-500">
              ID: {serverData.settings.server_id}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 md:grid md:grid-cols-3 md:gap-6">
          <div className="flex-1 flex-grow min-w-[80px] bg-gray-50 rounded-lg p-2 md:min-w-0 md:p-4">
            <h4 className="text-xs md:text-sm font-medium text-gray-500 mb-1 md:mb-2">
              ポイント単位
            </h4>
            <p className="text-sm md:text-lg font-medium">
              {globalSettings.point_unit}
            </p>
            <h4 className="text-xs md:text-sm font-medium text-gray-500">
              プール数 {globalSettings.point_units?.length ?? 0}
            </h4>
          </div>
          <div className="flex-1 flex-grow min-w-[80px] bg-gray-50 rounded-lg p-2 md:min-w-0 md:p-4">
            <h4 className="text-xs md:text-sm font-medium text-gray-500 mb-1 md:mb-2">
              タイムゾーン
            </h4>
            <p className="text-sm md:text-lg font-medium">
              {globalSettings.timezone}
            </p>
          </div>
          <div className="flex-1 flex-grow min-w-[80px] bg-gray-50 rounded-lg p-2 md:min-w-0 md:p-4">
            <h4 className="text-xs md:text-sm font-medium text-gray-500 mb-1 md:mb-2">
              言語
            </h4>
            <p className="text-sm md:text-lg font-medium">
              {globalSettings.language}
            </p>
          </div>

          {/* ポイントプールセクション */}
          {globalSettings.point_units?.map((unit, index) => {
            const linkedFeatures = getLinkedFeatures(
              unit.unit_id,
              serverData.settings.feature_settings
            );

            return (
              <div
                key={unit.unit_id ?? index}
                className="w-full md:flex-1 md:flex-grow min-w-[80px] bg-white rounded-lg shadow-sm p-2 mb-4 md:mb-0 md:min-w-0 md:p-4"
              >
                <h4 className="text-xs md:text-sm font-medium text-gray-500 mb-1 md:mb-2">
                  プール {index + 1}
                </h4>
                <p className="text-sm md:text-lg font-medium mt-2">
                  {unit.name || '未定義'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  ID: <span className="font-mono">{unit.unit_id ?? '未設定'}</span>
                </p>

                {linkedFeatures.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-xs md:text-sm font-medium text-gray-500 mb-1">
                      紐づく機能:
                    </h4>
                    <ul className="list-disc pl-5">
                      {linkedFeatures.map((feature) => (
                        <li key={feature.type}>
                          <span className="font-medium">{feature.name}:</span>
                          <ul className="list-disc pl-5 text-xs text-gray-600">
                            {feature.details.map((detail, i) => (
                              <li key={i}>{detail}</li>
                            ))}
                          </ul>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </EditableFeatureCard>
  );
};

export default ServerInfo;