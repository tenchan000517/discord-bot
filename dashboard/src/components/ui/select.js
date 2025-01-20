import React from 'react';

export const Select = ({ 
    value, 
    onChange, 
    children, 
    className = '', 
    multiple = false,
    disabled = false,
    ...props 
}) => {
    // 値の正規化
    const normalizeValue = (inputValue) => {
        if (multiple) {
            // 複数選択の場合
            if (!Array.isArray(inputValue)) {
                return [];
            }
            return inputValue;
        }
        // 単一選択の場合
        if (inputValue === null || inputValue === undefined) {
            return '';
        }
        return inputValue;
    };

    const handleChange = (e) => {
        if (!onChange) return;

        if (multiple) {
            // 複数選択の場合は選択された値の配列を返す
            const selectedValues = Array.from(e.target.selectedOptions, option => option.value);
            onChange(selectedValues);
        } else {
            // 単一選択の場合は従来通り
            onChange(e);
        }
    };

    return (
        <select
            value={normalizeValue(value)}
            onChange={handleChange}
            className={`w-full p-2 border border-gray-300 rounded-md 
                focus:outline-none focus:ring-2 focus:ring-blue-500 
                disabled:bg-gray-100 disabled:cursor-not-allowed
                ${className}`}
            multiple={multiple}
            disabled={disabled}
            {...props}
        >
            {children}
        </select>
    );
};
