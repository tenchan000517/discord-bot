import React from 'react';

export const Select = ({ value, onChange, children, className = '', ...props }) => {
    console.log('Select component props:', { value, hasOnChange: !!onChange, className, otherProps: props });

    const handleChange = (e) => {
        console.log('Select handleChange:', e);
        console.log('Select new value:', e.target.value);
        if (onChange) {
            onChange(e);
        }
    };

    return (
        <select
            value={value}
            onChange={handleChange}
            className={`w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
            {...props}
        >
            {children}
        </select>
    );
};