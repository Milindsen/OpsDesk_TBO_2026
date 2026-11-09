import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import type { AuthResponse, Role, User } from '../api/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<void>;
  logout: () => void;
  isRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('opsdesk_token'));
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem('opsdesk_user');
    if (raw) {
      try {
        return JSON.parse(raw) as User;
      } catch {
        return null;
      }
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMe = async () => {
      const storedToken = localStorage.getItem('opsdesk_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await apiClient.get<User>('/me');
        setUser(res.data);
        localStorage.setItem('opsdesk_user', JSON.stringify(res.data));
      } catch {
        if (!localStorage.getItem('opsdesk_user')) {
          localStorage.removeItem('opsdesk_token');
          setToken(null);
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchMe();
  }, [token]);

  const login = async (email: string, password = 'password123') => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login', {
        email,
        password,
      });
      const data = response.data;
      localStorage.setItem('opsdesk_token', data.access_token);
      localStorage.setItem('opsdesk_user', JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('opsdesk_token');
    localStorage.removeItem('opsdesk_user');
    setToken(null);
    setUser(null);
  };

  const isRole = (...roles: Role[]): boolean => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, isRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
