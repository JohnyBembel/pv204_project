// AuthContext.js
import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState('');
  const [userPublicKey, setUserPublicKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');

  // Token validation function that only uses state within this component
  const validateToken = async (token) => {
    try {
      const response = await fetch(`http://localhost:8000/auth/validate?session-token=${encodeURIComponent(token)}`);
      
      if (!response.ok) {
        // Token is invalid or expired, clear localStorage
        logout();
        setStatus('Your session has expired. Please login again.');
        return false;
      } else {
        setStatus('Authentication successful');
        return true;
      }
    } catch (error) {
      logout();
      setStatus('Error validating session. Please login again.');
      return false;
    }
  };
  
  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('authToken');
    const pubKey = localStorage.getItem('userPublicKey');
    
    if (token && pubKey) {
      setAuthToken(token);
      setUserPublicKey(pubKey);
      setIsLoggedIn(true);
      
      // Validate token
      validateToken(token);
    }
    
    setLoading(false);
  }, []);
  
  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userPublicKey');
    setAuthToken('');
    setUserPublicKey('');
    setIsLoggedIn(false);
  };
  
  return (
    <AuthContext.Provider value={{ 
      isLoggedIn, 
      authToken, 
      userPublicKey,
      setAuthToken,
      setUserPublicKey,
      setIsLoggedIn,
      logout,
      loading,
      status,
      setStatus,
      validateToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};