import { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

// Centralized helper for authenticated fetch calls with Bearer token
export const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem('mediguide_token');
  const headers = new Headers(options.headers || {});
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });
  
  // If unauthorized, clear invalid token
  if (response.status === 401 && !url.includes('/api/auth/login')) {
    localStorage.removeItem('mediguide_auth');
    localStorage.removeItem('mediguide_token');
    window.dispatchEvent(new Event('mediguide_logout'));
  }
  
  return response;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('mediguide_auth');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('mediguide_auth');
      }
    }
    setLoading(false);

    const handleExternalLogout = () => {
      setUser(null);
    };
    window.addEventListener('mediguide_logout', handleExternalLogout);
    return () => window.removeEventListener('mediguide_logout', handleExternalLogout);
  }, []);

  const login = async (email, password = '') => {
    // Attempt backend authentication
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password: password || 'patient123' })
      });

      if (res.ok) {
        const data = await res.json();
        const authData = {
          isAuthenticated: true,
          token: data.token,
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          role: data.user.role,
          specialty: data.user.specialty,
        };
        localStorage.setItem('mediguide_token', data.token);
        localStorage.setItem('mediguide_auth', JSON.stringify(authData));
        setUser(authData);
        return authData;
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Invalid email or password.');
      }
    } catch (err) {
      // If server unreachable or error, throw to let UI display error
      throw err;
    }
  };

  const quickLogin = async (role) => {
    const credentials = {
      patient: { email: 'alex@example.com', password: 'patient123' },
      doctor: { email: 'sarah@example.com', password: 'doctor123' },
      admin: { email: 'admin@example.com', password: 'admin123' }
    };
    const cred = credentials[role] || credentials.patient;
    return await login(cred.email, cred.password);
  };

  const logout = () => {
    localStorage.removeItem('mediguide_auth');
    localStorage.removeItem('mediguide_token');
    setUser(null);
  };

  if (loading) return null;

  return (
    <AuthContext.Provider value={{ user, login, quickLogin, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

