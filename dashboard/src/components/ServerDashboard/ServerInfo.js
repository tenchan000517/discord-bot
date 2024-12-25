import React from 'react';
import { EditableFeatureCard } from '../EditableFeatureCard';
import { ServerSettingsForm } from '../EditForms/ServerSettingsForm';

const ServerInfo = ({
    serverData,
    selectedServer,
    editingSection,
    setEditingSection,
    handleUpdateSettings,
  }) => {
    if (!serverData || !selectedServer) return null;
  
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
            onSubmit={(data) => handleUpdateSettings('server-settings', data)}
          />
        }
      >
        <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-6 mb-8">
            {selectedServer.icon ? (
              <img
                src={`https://cdn.discordapp.com/icons/${serverData.settings.server_id}/${selectedServer.icon}.png`}
                alt="Server Icon"
                className="w-20 h-20 rounded-full ring-2 ring-gray-100"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <span className="text-3xl text-white font-medium">
                  {selectedServer.name.charAt(0)}
                </span>
              </div>
            )}
            <div>
              <h3 className="text-2xl font-bold mb-1">{selectedServer.name}</h3>
              <p className="text-gray-500">ID: {serverData.settings.server_id}</p>
            </div>
          </div>
  
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">ポイント単位</h4>
              <p className="text-lg font-medium">
                {serverData.settings.global_settings.point_unit}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">タイムゾーン</h4>
              <p className="text-lg font-medium">
                {serverData.settings.global_settings.timezone}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-500 mb-2">言語</h4>
              <p className="text-lg font-medium">
                {serverData.settings.global_settings.language}
              </p>
            </div>
          </div>
        </div>
      </EditableFeatureCard>
    );
  };
  
  export default ServerInfo;
