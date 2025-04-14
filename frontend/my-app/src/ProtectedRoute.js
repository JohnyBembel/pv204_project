// ProtectedRoute.js
import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom'; // Remove Route if not using it
import { AuthContext } from './AuthContext';

const ProtectedRoute = ({ element, ...rest }) => {
    const { isLoggedIn, loading } = useContext(AuthContext);
    
    if (loading) {
        return <div>Loading...</div>;
    }
    
    return isLoggedIn ? element : <Navigate to="/auth" />;
};

export default ProtectedRoute;