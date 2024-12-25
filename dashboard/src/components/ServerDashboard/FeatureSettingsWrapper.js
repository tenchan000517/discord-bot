'use client';

import React, { useState, useEffect } from 'react';
import { BattleSettingsForm } from '../EditForms/BattleSettingsForm';
import { GachaSettingsForm } from '../EditForms/GachaSettingsForm';
import { FortuneSettingsForm } from '../EditForms/FortuneSettingsForm';

const FeatureSettingsWrapper = ({ settings, pointUnit, onSubmit }) => {
  const [formData, setFormData] = useState({
    battle: settings.feature_settings.battle,
    gacha: settings.feature_settings.gacha,
    fortune: settings.feature_settings.fortune,
  });

  useEffect(() => {
    onSubmit({
      ...settings,
      feature_settings: formData,
    });
  }, [formData, settings, onSubmit]);

  const handleSettingsChange = (section, newData) => {
    setFormData((prevData) => ({
      ...prevData,
      [section]: newData,
    }));
  };

  return (
    <div className="space-y-8">
      <BattleSettingsForm
        settings={formData.battle}
        pointUnit={pointUnit}
        onChange={(data) => handleSettingsChange('battle', data)}
      />
      <GachaSettingsForm
        settings={formData.gacha}
        pointUnit={pointUnit}
        onChange={(data) => handleSettingsChange('gacha', data)}
      />
      <FortuneSettingsForm
        settings={formData.fortune}
        onChange={(data) => handleSettingsChange('fortune', data)}
      />
    </div>
  );
};

export default FeatureSettingsWrapper;
