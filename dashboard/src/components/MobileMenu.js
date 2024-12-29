'use client';

import React from 'react';
import { X } from 'lucide-react';

const MobileMenu = ({ isOpen, onClose, menuItems, selectedMenu, setSelectedMenu }) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      
      {/* Slide-out menu */}
      <div 
        className={`
          fixed top-0 right-0 h-full w-64 bg-white z-50 transform transition-transform duration-300 ease-in-out
          lg:hidden ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="メインメニュー"
      >
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-lg font-medium">メニュー</h2>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-100 rounded-full"
            aria-label="メニューを閉じる"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <nav className="p-2">
          {menuItems.map((group) => (
            <div key={group.category} className="mb-4">
              <div className="px-4 py-2 text-sm font-medium text-gray-500">
                {group.category}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setSelectedMenu(item.id);
                      onClose();
                    }}
                    className={`w-full flex items-center px-4 py-3 rounded-lg text-left transition-colors 
                      ${selectedMenu === item.id ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'}`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>
    </>
  );
};

export default MobileMenu;