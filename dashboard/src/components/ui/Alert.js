// components/Alert.js
import React from 'react';

export const Alert = ({ children, variant = 'error' }) => {
  const styles = {
    error: 'bg-red-50 border-l-4 border-red-500 text-red-700',
    warning: 'bg-yellow-50 border-l-4 border-yellow-500 text-yellow-700',
    success: 'bg-green-50 border-l-4 border-green-500 text-green-700',
    info: 'bg-blue-50 border-l-4 border-blue-500 text-blue-700'
  };

  return (
    <div className={`${styles[variant]} p-4`} role="alert">
      {children}
    </div>
  );
};