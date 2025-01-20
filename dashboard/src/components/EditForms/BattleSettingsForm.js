// components/EditForms/BattleSettingsForm.js
import React, { useState, useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';
import { Switch } from '../ui/switch';
import { Select } from '../ui/select';

export const BattleSettingsForm = ({ settings, pointUnit, serverRoles, onChange }) => {
  const [formData, setFormData] = useState({
    enabled: settings.enabled,
    required_role_id: settings.required_role_id,
    winner_role_id: settings.winner_role_id,
    points_enabled: settings.points_enabled,
    points_per_kill: settings.points_per_kill,
    winner_points: settings.winner_points,
    start_delay_minutes: settings.start_delay_minutes
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newData = {
      ...formData,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value, 10) : value
    };
    setFormData(newData);
    onChange(newData);
  };

  useEffect(() => {
    setFormData({
      enabled: settings.enabled,
      required_role_id: settings.required_role_id,
      winner_role_id: settings.winner_role_id,
      points_enabled: settings.points_enabled,
      points_per_kill: settings.points_per_kill,
      winner_points: settings.winner_points,
      start_delay_minutes: settings.start_delay_minutes
    });
  }, [settings]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-medium">バトル機能</h3>
          <p className="text-sm text-gray-500">バトル機能の有効/無効を切り替えます</p>
        </div>
        <Switch
          checked={formData.enabled}
          onCheckedChange={(checked) => handleChange({ target: { name: 'enabled', type: 'checkbox', checked }})}
        />
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList>
          <TabsTrigger value="general">基本設定</TabsTrigger>
          <TabsTrigger value="points">ポイント設定</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              参加に必要なロール
            </label>
            <Select
              value={formData.required_role_id || ''}
              onChange={(e) => handleChange({ target: { name: 'required_role_id', value: e.target.value }})}
            >
              <option value="">制限なし</option>
              {serverRoles?.map((role) => (
                <option key={role.id} value={role.id}>{role.name}</option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              勝者に付与するロール
            </label>
            <Select
              value={formData.winner_role_id || ''}
              onChange={(e) => handleChange({ target: { name: 'winner_role_id', value: e.target.value }})}
            >
              <option value="">付与しない</option>
              {serverRoles?.map((role) => (
                <option key={role.id} value={role.id}>{role.name}</option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              開始遅延（分）
            </label>
            <input
              type="number"
              name="start_delay_minutes"
              value={formData.start_delay_minutes}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </TabsContent>

        <TabsContent value="points" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-gray-700">ポイント機能</h4>
              <p className="text-sm text-gray-500">ポイントの付与を有効にします</p>
            </div>
            <Switch
              checked={formData.points_enabled}
              onCheckedChange={(checked) => handleChange({ target: { name: 'points_enabled', type: 'checkbox', checked }})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              キル報酬
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                name="points_per_kill"
                value={formData.points_per_kill}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={!formData.points_enabled}
              />
              <span className="text-gray-600">{pointUnit}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              勝者報酬
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                name="winner_points"
                value={formData.winner_points}
                onChange={handleChange}
                min="0"
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={!formData.points_enabled}
              />
              <span className="text-gray-600">{pointUnit}</span>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};