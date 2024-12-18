import React, { useState } from 'react';
import { PencilIcon } from 'lucide-react';

export const EditableFeatureCard = ({ 
  title, 
  children, 
  onSave,
  isEditing,
  onEditToggle,
  editForm,
  canEdit = true 
}) => {
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // editFormからデータを取得してonSaveに渡す
      if (editForm?.props?.onSubmit) {
        const formData = await editForm.props.onSubmit();
        await onSave(formData);
      } else {
        await onSave();
      }
      onEditToggle(); // 保存成功後に編集モードを終了
    } catch (error) {
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="flex justify-between items-center mb-4 pb-2 border-b">
        <h2 className="text-xl font-semibold">{title}</h2>
        {canEdit && (
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  {isSaving ? '保存中...' : '保存'}
                </button>
                <button
                  onClick={onEditToggle}
                  disabled={isSaving}
                  className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  キャンセル
                </button>
              </>
            ) : (
              <button
                onClick={onEditToggle}
                className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <PencilIcon className="w-5 h-5" />
              </button>
            )}
          </div>
        )}
      </div>
      {isEditing ? editForm : children}
    </div>
  );
};