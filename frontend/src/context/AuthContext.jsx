import { createContext, useState, useContext, useEffect } from 'react';
import { mockUsers } from '../data/mockData';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('mediguide_auth');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = (email, role) => {
    let userName = email.split('@')[0];
    
    // Attempt to match mock user names if it's a known demo role
    if (role === 'patient') userName = 'Alex Morgan';
    if (role === 'doctor') userName = 'Dr. Sarah Wilson';
    if (role === 'admin') userName = 'System Administrator';

    const authData = {
      isAuthenticated: true,
      email,
      role,
      name: userName
    };
    
    localStorage.setItem('mediguide_auth', JSON.stringify(authData));
    setUser(authData);
  };

  const logout = () => {
    localStorage.removeItem('mediguide_auth');
    setUser(null);
  };

  if (loading) return null; // or a spinner

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
