// src/components/ui/label.js
import React from 'react';

export const Label = ({ children, htmlFor, className, ...props }) => (
    <label
        htmlFor={htmlFor}
        className={`block text-sm font-medium text-gray-700 ${className}`}
        {...props}
    >
        {children}
    </label>
);
