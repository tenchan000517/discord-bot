// src/components/ui/switch.js
import React from 'react';

export const Switch = ({ checked, onCheckedChange, className, ...props }) => (
    <label className={`inline-flex items-center cursor-pointer ${className}`}>
        <input
            type="checkbox"
            checked={checked}
            onChange={(e) => onCheckedChange(e.target.checked)}
            className="sr-only"
            {...props}
        />
        <span
            className={`w-10 h-6 flex items-center bg-gray-200 rounded-full p-1 duration-300 ease-in-out ${checked ? 'bg-blue-500' : ''}`}
        >
            <span
                className={`bg-white w-4 h-4 rounded-full shadow-md transform duration-300 ease-in-out ${checked ? 'translate-x-4' : ''}`}
            />
        </span>
    </label>
);
