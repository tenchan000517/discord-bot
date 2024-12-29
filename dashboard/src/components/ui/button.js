// src/components/ui/button.js
import React from 'react';

export const Button = ({ children, onClick, className, variant = 'default', ...props }) => {
    const variants = {
        default: 'bg-blue-500 text-white hover:bg-blue-600',
        outline: 'bg-transparent border border-blue-500 text-blue-500 hover:bg-blue-500 hover:text-white',
    };

    return (
        <button
            onClick={onClick}
            className={`px-4 py-2 rounded-md transition-colors duration-200 ${variants[variant] || variants.default} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
};
