'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';
// import { authApi } from '@/lib/api';
import { authApi } from '../lib/api';

interface AuthContextType {
  user: any;
  loading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkUser();
  }, []);

  const checkUser = async () => {
    const token = Cookies.get('lifeos_token');
    if (token) {
      try {
        const { data } = await authApi.getMe();
        setUser(data);
      } catch (err) {
        logout();
      }
    }
    setLoading(false);
  };

  const login = (token: string) => {
    Cookies.set('lifeos_token', token);
    checkUser();
    router.push('/dashboard');
  };

  const logout = () => {
    Cookies.remove('lifeos_token');
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);