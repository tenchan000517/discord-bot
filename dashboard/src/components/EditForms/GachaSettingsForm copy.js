// components/EditForms/GachaSettingsForm.js
import React, { useState, useEffect } from 'react';
import { PlusIcon, XIcon, ImageIcon } from 'lucide-react';

export const GachaSettingsForm = ({ settings, pointUnit, onChange }) => {
    const [formData, setFormData] = useState({
        enabled: settings.enabled,
        use_daily_panel: settings.use_daily_panel ?? true,  // これを追加
        items: [...settings.items],
        messages: settings.messages || {
            setup: '',
            daily: '',
            win: '',
            custom_messages: {}
        },
        media: settings.media || {
            setup_image: '',
            banner_gif: '',
            gacha_animation_gif: ''
        }
    });
    const [activeTab, setActiveTab] = useState('items');

    const handleChange = (e) => {
        const { name, type, checked } = e.target;
        const newData = {
            ...formData,
            [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(e.target.value, 10) : e.target.value
        };
        setFormData(newData);
        onChange(newData);
    };

    const handleItemChange = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index] = {
            ...newItems[index],
            [field]: field === 'weight' || field === 'points' ? parseInt(value, 10) : value
        };
        const newData = { ...formData, items: newItems };
        setFormData(newData);
        onChange(newData);
    };

    const handleMessageChange = (field, value) => {
        const newMessages = {
            ...formData.messages,
            [field]: value
        };
        const newData = { ...formData, messages: newMessages };
        setFormData(newData);
        onChange(newData);
    };

    const handleMediaChange = (field, value) => {
        const newMedia = {
            ...formData.media,
            [field]: value
        };
        const newData = { ...formData, media: newMedia };
        setFormData(newData);
        onChange(newData);
    };

    const addItem = () => {
        const newData = {
            ...formData,
            items: [...formData.items, { name: '', points: 0, weight: 1, image_url: '' }]
        };
        setFormData(newData);
        onChange(newData);
    };

    const removeItem = (index) => {
        const newData = {
            ...formData,
            items: formData.items.filter((_, i) => i !== index)
        };
        setFormData(newData);
        onChange(newData);
    };

    const calculateTotalWeight = () => {
        return formData.items.reduce((sum, item) => sum + parseInt(item.weight, 10), 0);
    };

    const calculateProbability = (weight) => {
        const totalWeight = calculateTotalWeight();
        return ((weight / totalWeight) * 100).toFixed(1);
    };

    useEffect(() => {
        setFormData({
            enabled: settings.enabled,
            use_daily_panel: settings.use_daily_panel ?? true,  // これを追加
            items: [...settings.items],
            messages: settings.messages || {
                setup: '',
                daily: '',
                win: '',
                custom_messages: {}
            },
            media: settings.media || {
                setup_image: '',
                banner_gif: '',
                gacha_animation_gif: ''
            }
        });
    }, [settings]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="font-medium">ガチャ機能</h3>
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

            <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                    {['basic', 'items', 'messages', 'media'].map((tab) => (  // 'basic' を追加
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`py-2 px-4 border-b-2 font-medium text-sm ${activeTab === tab
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            {tab === 'basic' ? '基本設定' :  // 基本設定タブのラベル追加
                                tab === 'items' ? 'アイテム設定' :
                                    tab === 'messages' ? 'メッセージ設定' : 'メディア設定'}
                        </button>
                    ))}
                </nav>
            </div>

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

                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                            <h4 className="text-sm font-medium text-gray-700">デイリーパネルの表示</h4>
                            <p className="text-sm text-gray-500">常設のガチャパネルを使用するかどうかを設定します</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                name="use_daily_panel"
                                checked={formData.use_daily_panel}
                                onChange={handleChange}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                    </div>
                </div>
            )}

            {activeTab === 'items' && (
                <div className="space-y-4">
                    {formData.items.map((item, index) => (
                        <div key={index} className="flex gap-3 items-start">
                            <div className="flex-1 grid grid-cols-4 gap-2">
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

            {activeTab === 'messages' && (
                <div className="space-y-6">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">セットアップメッセージ</label>
                            <textarea
                                value={formData.messages.setup}
                                onChange={(e) => handleMessageChange('setup', e.target.value)}
                                placeholder="ガチャの初期設定時に表示されるメッセージ"
                                className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                rows="3"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">デイリーメッセージ</label>
                            <textarea
                                value={formData.messages.daily}
                                onChange={(e) => handleMessageChange('daily', e.target.value)}
                                placeholder="ガチャパネルに表示されるメッセージ"
                                className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                rows="3"
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                利用可能な変数: {'{user}'} - ユーザー名
                            </p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">当選メッセージ</label>
                            <textarea
                                value={formData.messages.win}
                                onChange={(e) => handleMessageChange('win', e.target.value)}
                                placeholder="ガチャ実行時の当選メッセージ"
                                className="mt-1 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                rows="3"
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                利用可能な変数: {'{user}'} - ユーザー名, {'{item}'} - 獲得アイテム名
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'media' && (
                <div className="space-y-6">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">セットアップ画像URL</label>
                            <div className="flex gap-2 mt-1">
                                <input
                                    type="text"
                                    value={formData.media.setup_image || ''}
                                    onChange={(e) => handleMediaChange('setup_image', e.target.value)}
                                    placeholder="https://example.com/setup-image.png"
                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                {formData.media.setup_image && (
                                    <img
                                        src={formData.media.setup_image}
                                        alt="Preview"
                                        className="w-8 h-8 object-cover rounded"
                                    />
                                )}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">バナーGIF URL</label>
                            <div className="flex gap-2 mt-1">
                                <input
                                    type="text"
                                    value={formData.media.banner_gif || ''}
                                    onChange={(e) => handleMediaChange('banner_gif', e.target.value)}
                                    placeholder="https://example.com/banner.gif"
                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                {formData.media.banner_gif && (
                                    <img
                                        src={formData.media.banner_gif}
                                        alt="Preview"
                                        className="w-8 h-8 object-cover rounded"
                                    />
                                )}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">ガチャ演出GIF URL</label>
                            <div className="flex gap-2 mt-1">
                                <input
                                    type="text"
                                    value={formData.media.gacha_animation_gif || ''}
                                    onChange={(e) => handleMediaChange('gacha_animation_gif', e.target.value)}
                                    placeholder="https://example.com/animation.gif"
                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                {formData.media.gacha_animation_gif && (
                                    <img
                                        src={formData.media.gacha_animation_gif}
                                        alt="Preview"
                                        className="w-8 h-8 object-cover rounded"
                                    />
                                )}
                            </div>
                            <p className="text-sm text-gray-500 mt-1">
                                ガチャを引く際に表示されるアニメーションGIF
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};