import React from 'react';

const LogoutButton = () => {
  const handleLogout = () => {
    // Clear all keys from localStorage
    localStorage.clear();
    // Refresh the page to reset application state
    window.location.reload();
  };

  return (
    <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>
      Logout
    </button>
  );
};

export default LogoutButton;
