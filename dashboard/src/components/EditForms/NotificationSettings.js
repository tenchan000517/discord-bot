import React, { useState, useEffect } from 'react';

const NotificationTypes = {
    CHANNEL: 'channel',
    DM: 'dm'
};

const TemplateVariables = {
    USER_MENTION: '{user_mention}',
    ROLE_MENTION: '{role_mention}',
    USER_NAME: '{user_name}',
    ROLE_NAME: '{role_name}',
    POINTS: '{points}',
    ACTION: '{action}',
    SERVER_NAME: '{server_name}',
    CHANNEL_NAME: '{channel_name}'
};

const NotificationSettings = ({
    notification,
    channels = [],
    serverRoles = [],
    onUpdate
}) => {
    // console.log('[6. Props Check] Channels passed to NotificationSettings:', channels); // ログ追加
    console.log("[DEBUG] NotificationSettings props.notification:", notification);

    const defaultNotification = {
        enabled: false,
        type: NotificationTypes.CHANNEL,
        channelId: '',
        messageTemplate: '',
        timing: {
            onSuccess: true,
            onFailure: false
        }
    };

    const [currentNotification, setCurrentNotification] = useState(
        notification ? { ...defaultNotification, ...notification } : defaultNotification
    );

    useEffect(() => {
        if (notification) {
            setCurrentNotification(prev => ({
                ...defaultNotification,
                ...notification
            }));
        }
    }, [notification]);

    const handleChange = (field, value) => {
        const updatedNotification = {
            ...currentNotification,
            [field]: value
        };
    
        setCurrentNotification(updatedNotification); // 修正済み
        console.log(`[DEBUG] NotificationSettings updated:`, updatedNotification); // ログ追加

        onUpdate(updatedNotification); // 修正済み
    };
    

    const handleTemplateInsert = (variable) => {
        if (!currentNotification.messageTemplate) {
            handleChange('messageTemplate', variable);
            return;
        }

        const textarea = document.querySelector('textarea[name="messageTemplate"]');
        if (textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const template = currentNotification.messageTemplate;
            const newTemplate = template.substring(0, start) + variable + template.substring(end);
            handleChange('messageTemplate', newTemplate);
            
            // カーソル位置を変数の後ろに移動
            setTimeout(() => {
                textarea.selectionStart = textarea.selectionEnd = start + variable.length;
                textarea.focus();
            }, 0);
        }
    };

    return (
        <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-4">通知設定</h4>
            <div className="space-y-4">
                {/* Toggle switch */}
                <div className="flex items-center justify-between mb-4">
                    <span className="text-sm text-gray-600">通知を有効にする</span>
                    <div className="relative inline-block w-10 align-middle select-none">
                        <input
                            type="checkbox"
                            checked={currentNotification.enabled}
                            onChange={(e) => handleChange('enabled', e.target.checked)}
                            className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                        />
                        <label className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer" />
                    </div>
                </div>

                {currentNotification.enabled && (
                    <>
                        {/* Notification type selection */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                通知タイプ
                            </label>
                            <select
                                value={currentNotification.type}
                                onChange={(e) => handleChange('type', e.target.value)}
                                className="w-full px-3 py-2 border rounded-md"
                            >
                                <option value={NotificationTypes.CHANNEL}>チャンネル通知</option>
                                <option value={NotificationTypes.DM}>ダイレクトメッセージ</option>
                            </select>
                        </div>

                        {/* チャンネル選択 */}
                        {currentNotification.type === NotificationTypes.CHANNEL && (
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    通知チャンネル
                                </label>
                                <select
                                    value={currentNotification.channelId}
                                    onChange={(e) => handleChange('channelId', e.target.value)}
                                    className="w-full px-3 py-2 border rounded-md"
                                >
                                    <option value="">チャンネルを選択してください</option>
                                    {channels.map((channel) => (
                                        <option key={channel.id} value={channel.id}>
                                            {channel.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* メッセージテンプレート */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">
                                メッセージテンプレート
                            </label>
                            <div className="flex flex-wrap gap-2 mb-2">
                                {Object.entries(TemplateVariables).map(([key, value]) => (
                                    <button
                                        key={key}
                                        onClick={() => handleTemplateInsert(value)}
                                        className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                                        type="button"
                                    >
                                        {value}
                                    </button>
                                ))}
                            </div>
                            <textarea
                                value={notification?.messageTemplate || ''}
                                onChange={(e) => handleChange('messageTemplate', e.target.value)}
                                placeholder="通知メッセージのテンプレートを入力"
                                className="w-full px-3 py-2 border rounded-md"
                                rows={3}
                            />
                            <p className="text-xs text-gray-500">
                                上記の変数を使用してメッセージをカスタマイズできます
                            </p>
                        </div>

                        {/* 通知タイミング */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">通知タイミング</label>
                            <div className="space-y-2">
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={notification?.timing?.onSuccess || false}
                                        onChange={(e) => handleChange('timing', {
                                            ...notification?.timing,
                                            onSuccess: e.target.checked
                                        })}
                                        className="mr-2"
                                    />
                                    <span className="text-sm">アクション成功時</span>
                                </label>
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={notification?.timing?.onFailure || false}
                                        onChange={(e) => handleChange('timing', {
                                            ...notification?.timing,
                                            onFailure: e.target.checked
                                        })}
                                        className="mr-2"
                                    />
                                    <span className="text-sm">アクション失敗時</span>
                                </label>
                            </div>
                        </div>

                        {/* プレビュー */}
                        <div className="p-4 bg-gray-50 rounded-lg">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">プレビュー</h5>
                            <p className="text-sm text-gray-600 whitespace-pre-wrap">
                                {notification?.messageTemplate?.replace(/\{([^}]+)\}/g, (match) => {
                                    switch (match) {
                                        case '{user_mention}': return '@ユーザー';
                                        case '{role_mention}': return '@ロール';
                                        case '{user_name}': return 'ユーザー名';
                                        case '{role_name}': return 'ロール名';
                                        case '{points}': return '100';
                                        case '{action}': return 'アクション';
                                        case '{server_name}': return 'サーバー名';
                                        case '{channel_name}': return 'チャンネル名';
                                        default: return match;
                                    }
                                }) || '通知メッセージのプレビューがここに表示されます'}
                            </p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default NotificationSettings;