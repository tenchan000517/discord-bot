// components/EditForms/GachaSettingsForm.js
import React, { useState, useEffect } from 'react';
import { PlusIcon, XIcon, ImageIcon } from 'lucide-react';
import { validateAndNormalizeGachaSettings, createNewGachaTemplate } from '@/utils/gachaHelper';

export const GachaSettingsForm = ({ settings, pointUnit, onChange, serverData, serverId }) => {
    const [selectedGachaId, setSelectedGachaId] = useState('');
    const [formData, setFormData] = useState(null);
    const [activeTab, setActiveTab] = useState('basic');

    // 正規化された設定を取得
    const normalizedSettings = validateAndNormalizeGachaSettings(settings);

    const handleGachaSelect = (e) => {
        const newSelectedId = e.target.value;
        setSelectedGachaId(newSelectedId);

        if (!newSelectedId) {
            setFormData(null);
            return;
        }

        const selectedGacha = normalizedSettings.gacha_list.find(
            gacha => gacha.gacha_id === newSelectedId
        );

        if (selectedGacha) {
            setFormData({ ...selectedGacha });
        }
    };

    const handleDeleteGacha = async () => {
        if (!selectedGachaId || !formData) return;

        if (!confirm('このガチャを削除してもよろしいですか？この操作は取り消せません。')) {
            return;
        }

        try {
            const response = await fetch(
                `/api/servers/${serverId}/settings?gachaId=${selectedGachaId}`,
                {
                    method: 'DELETE',
                }
            );

            if (!response.ok) {
                throw new Error('Failed to delete gacha');
            }

            const updatedGachaList = normalizedSettings.gacha_list.filter(
                gacha => gacha.gacha_id !== selectedGachaId
            );

            onChange({
                ...normalizedSettings,
                gacha_list: updatedGachaList
            });

            setSelectedGachaId('');
            setFormData(null);

            alert('ガチャが正常に削除されました。');
        } catch (error) {
            console.error('Error deleting gacha:', error);
            alert('ガチャの削除中にエラーが発生しました。');
        }
    };

    const handleChange = (e) => {
        if (!formData) return;

        const { name, type, checked, value } = e.target;
        const newData = {
            ...formData,
            [name]: type === 'checkbox' ? checked : value
        };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const handleSubscriptionChange = (e) => {
        if (!formData) return;

        const { name, type, checked, value } = e.target;
        const newSubscription = {
            ...formData.subscription,
            [name]: type === 'checkbox' ? checked : value
        };

        const newData = {
            ...formData,
            subscription: newSubscription
        };

        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const handleItemChange = (index, field, value) => {
        if (!formData) return;

        const newItems = [...formData.items];
        if (field === 'message_settings') {
            newItems[index] = {
                ...newItems[index],
                message_settings: {
                    ...newItems[index].message_settings,
                    ...value
                }
            };
        } else {
            newItems[index] = {
                ...newItems[index],
                [field]: field === 'weight' || field === 'points' ? parseInt(value, 10) : value
            };
        }

        const newData = { ...formData, items: newItems };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const handleMessageChange = (field, value) => {
        if (!formData) return;

        const newMessages = {
            ...formData.messages,
            [field]: value
        };
        const newData = { ...formData, messages: newMessages };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const handleMediaChange = (field, value) => {
        if (!formData) return;

        const newMedia = {
            ...formData.media,
            [field]: value
        };
        const newData = { ...formData, media: newMedia };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const addItem = () => {
        if (!formData) return;

        const newData = {
            ...formData,
            items: [...formData.items, {
                name: '',
                points: 0,
                weight: 1,
                image_url: '',
                message_settings: {
                    enabled: false,
                    message: '{user}さん、{item}を獲得しました！'
                }
            }]
        };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const removeItem = (index) => {
        if (!formData) return;

        const newData = {
            ...formData,
            items: formData.items.filter((_, i) => i !== index)
        };
        setFormData(newData);

        const updatedGachaList = normalizedSettings.gacha_list.map(gacha =>
            gacha.gacha_id === selectedGachaId ? newData : gacha
        );
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });
    };

    const calculateTotalWeight = () => {
        if (!formData?.items) return 0;
        return formData.items.reduce((sum, item) => sum + parseInt(item.weight, 10), 0);
    };

    const calculateProbability = (weight) => {
        const totalWeight = calculateTotalWeight();
        if (totalWeight === 0) return '0.0';
        return ((weight / totalWeight) * 100).toFixed(1);
    };

    // 新規ガチャ作成
    const handleCreateNewGacha = () => {
        const defaultPointUnitId = serverData?.settings?.global_settings?.point_units?.[0]?.unit_id || "1";
        const newGacha = createNewGachaTemplate(defaultPointUnitId);

        const updatedGachaList = [...normalizedSettings.gacha_list, newGacha];
        onChange({
            ...normalizedSettings,
            gacha_list: updatedGachaList
        });

        setSelectedGachaId(newGacha.gacha_id);
        setFormData(newGacha);
    };

    useEffect(() => {
        if (!settings?.gacha_list?.length) return;
        const initialGacha = settings.gacha_list[0];
        setSelectedGachaId(initialGacha.gacha_id);
        setFormData(initialGacha);
    }, [settings]);

    return (
        <div className="space-y-6">
            {/* ガチャ選択またはヘッダー部分 */}
            <div className="flex items-center justify-between gap-4">
                <select
                    value={selectedGachaId}
                    onChange={handleGachaSelect}
                    className="flex-grow px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                    <option value="">ガチャを選択してください</option>
                    {normalizedSettings.gacha_list?.map((gacha) => (
                        <option key={gacha.gacha_id} value={gacha.gacha_id}>
                            {gacha.name || `ガチャ #${gacha.gacha_id.slice(0, 8)}`}
                        </option>
                    ))}
                </select>
                <button
                    onClick={handleCreateNewGacha}
                    className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                >
                    新規作成
                </button>
            </div>

            {formData && (
                <>
                    {/* タブナビゲーション */}
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            {['basic', 'items', 'messages', 'media', 'subscription'].map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`py-2 px-4 border-b-2 font-medium text-sm ${activeTab === tab
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }`}
                                >
                                    {tab === 'basic' ? '基本設定' :
                                        tab === 'items' ? 'アイテム設定' :
                                            tab === 'messages' ? 'メッセージ設定' :
                                                tab === 'media' ? 'メディア設定' : ''}

                                </button>
                            ))}
                        </nav>
                    </div>

                    {/* 基本設定タブ */}
                    {activeTab === 'basic' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <h4 className="text-sm font-medium text-gray-700">機能の有効化</h4>
                                    <p className="text-sm text-gray-500">ガチャ機能全体の有効/無効を設定します</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="enabled"
                                        checked={formData.enabled}
                                        onChange={handleChange}
                                        className="sr-only peer"
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            {/* その他の基本設定フィールド */}
                            <div className="space-y-4">
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">ガチャ名</h4>
                                    <input
                                        type="text"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        placeholder="ガチャ名を入力"
                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>

                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">ポイント単位</h4>
                                    <select
                                        name="point_unit_id"
                                        value={formData.point_unit_id}
                                        onChange={handleChange}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {serverData?.settings?.global_settings?.point_units?.map((unit) => (
                                            <option key={unit.unit_id} value={unit.unit_id}>
                                                {unit.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">表示チャンネル</h4>
                                    <select
                                        name="channel_id"
                                        value={formData.channel_id || ''}
                                        onChange={handleChange}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="">チャンネルを選択</option>
                                        {serverData?.channels?.map((channel) => (
                                            <option key={channel.id} value={channel.id}>
                                                {channel.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* アイテム設定タブ */}
                    {activeTab === 'items' && (
                        <div className="space-y-4">
                            {formData.items.map((item, index) => (
                                <div key={index} className="flex gap-3 items-start">
                                    <div className="flex-1 space-y-4">
                                        {/* 基本情報の行 */}
                                        <div className="grid grid-cols-4 gap-2">
                                            <div>
                                                <input
                                                    type="text"
                                                    value={item.name}
                                                    onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                                                    placeholder="アイテム名"
                                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <input
                                                        type="number"
                                                        value={item.points}
                                                        onChange={(e) => handleItemChange(index, 'points', e.target.value)}
                                                        placeholder="ポイント"
                                                        min="0"
                                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                    />
                                                    <span className="text-gray-600 whitespace-nowrap">{pointUnit}</span>
                                                </div>
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <input
                                                        type="number"
                                                        value={item.weight}
                                                        onChange={(e) => handleItemChange(index, 'weight', e.target.value)}
                                                        placeholder="重み"
                                                        min="1"
                                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                    />
                                                    <span className="text-gray-600 whitespace-nowrap">
                                                        {calculateProbability(item.weight)}%
                                                    </span>
                                                </div>
                                            </div>
                                            <div>
                                                <input
                                                    type="text"
                                                    value={item.image_url || ''}
                                                    onChange={(e) => handleItemChange(index, 'image_url', e.target.value)}
                                                    placeholder="画像URL"
                                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                />
                                            </div>
                                        </div>

                                        {/* メッセージ設定 */}
                                        <div className="bg-gray-50 p-4 rounded-lg">
                                            <div className="flex items-center justify-between mb-3">
                                                <h5 className="text-sm font-medium text-gray-700">当選メッセージ設定</h5>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={item.message_settings?.enabled ?? false}
                                                        onChange={(e) => handleItemChange(index, 'message_settings', { enabled: e.target.checked })}
                                                        className="sr-only peer"
                                                    />
                                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                </label>
                                            </div>
                                            {item.message_settings?.enabled && (
                                                <div>
                                                    <input
                                                        type="text"
                                                        value={item.message_settings?.message || ''}
                                                        onChange={(e) => handleItemChange(index, 'message_settings', { message: e.target.value })}
                                                        placeholder="当選メッセージを入力 ({user}と{item}が使用可能)"
                                                        className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => removeItem(index)}
                                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    >
                                        <XIcon className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}

                            <button
                                onClick={addItem}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
                            >
                                <PlusIcon className="w-5 h-5" />
                                <span>アイテムを追加</span>
                            </button>
                        </div>
                    )}

                    {/* メッセージ設定タブ */}
                    {activeTab === 'messages' && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">デイリーメッセージ</label>
                                <textarea
                                    value={formData.messages.daily}
                                    onChange={(e) => handleMessageChange('daily', e.target.value)}
                                    placeholder="ガチャパネルに表示されるメッセージ"
                                    className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    rows="3"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">X投稿メッセージ</label>
                                <textarea
                                    value={formData.messages.tweet_message}
                                    onChange={(e) => handleMessageChange('tweet_message', e.target.value)}
                                    placeholder="X（Twitter）に投稿する際の追加メッセージ"
                                    className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    rows="3"
                                />
                            </div>
                        </div>
                    )}

                    {/* メディア設定タブ */}
                    {activeTab === 'media' && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">セットアップ画像URL</label>
                                <input
                                    type="text"
                                    value={formData.media.setup_image || ''}
                                    onChange={(e) => handleMediaChange('setup_image', e.target.value)}
                                    placeholder="https://example.com/setup-image.png"
                                    className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">バナーGIF URL</label>
                                <input
                                    type="text"
                                    value={formData.media.banner_gif || ''}
                                    onChange={(e) => handleMediaChange('banner_gif', e.target.value)}
                                    placeholder="https://example.com/banner.gif"
                                    className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">ガチャ演出GIF URL</label>
                                <input
                                    type="text"
                                    value={formData.media.gacha_animation_gif || ''}
                                    onChange={(e) => handleMediaChange('gacha_animation_gif', e.target.value)}
                                    placeholder="https://example.com/animation.gif"
                                    className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                        </div>
                    )}

                    {/* サブスクリプション設定タブ
                    {activeTab === 'subscription' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <h4 className="text-sm font-medium text-gray-700">サブスクリプションの有効化</h4>
                                    <p className="text-sm text-gray-500">このガチャをサブスクリプション制にします</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="enabled"
                                        checked={formData.subscription?.enabled ?? false}
                                        onChange={(e) => handleSubscriptionChange(e)}
                                        className="sr-only peer"
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            {formData.subscription?.enabled && (
                                <>
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="text-sm font-medium text-gray-700 mb-2">価格設定</h4>
                                        <div className="flex gap-2">
                                            <input
                                                type="number"
                                                name="price"
                                                value={formData.subscription?.price ?? 0}
                                                onChange={handleSubscriptionChange}
                                                min="0"
                                                step="0.01"
                                                className="w-1/2 px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            />
                                            <select
                                                name="currency"
                                                value={formData.subscription?.currency ?? 'USD'}
                                                onChange={handleSubscriptionChange}
                                                className="w-1/2 px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            >
                                                <option value="USD">USD</option>
                                                <option value="JPY">JPY</option>
                                                <option value="EUR">EUR</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="text-sm font-medium text-gray-700 mb-2">課金間隔</h4>
                                        <select
                                            name="interval"
                                            value={formData.subscription?.interval ?? 'month'}
                                            onChange={handleSubscriptionChange}
                                            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        >
                                            <option value="day">日単位</option>
                                            <option value="week">週単位</option>
                                            <option value="month">月単位</option>
                                            <option value="year">年単位</option>
                                        </select>
                                    </div>
                                </>
                            )}
                        </div>
                    )} */}

                    {/* 削除ボタン */}
                    {activeTab === 'basic' && (
                        <div className="p-4 bg-red-50 rounded-lg">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="text-sm font-medium text-red-700">ガチャの削除</h4>
                                    <p className="text-sm text-red-600">このガチャを完全に削除します。この操作は取り消せません。</p>
                                </div>
                                <button
                                    onClick={handleDeleteGacha}
                                    className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
                                >
                                    削除
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};