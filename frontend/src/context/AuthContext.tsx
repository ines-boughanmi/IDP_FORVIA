import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { getCurrentUser, login as loginRequest } from '@/services/backendApi';
import { decodeJwt, isTokenExpired } from '@/utils/jwt';

type User = {
  id: number;
  username: string;
  email: string;
  role: string;
};

type AuthContextValue = {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      const storedToken = localStorage.getItem('access_token');
      if (!storedToken || isTokenExpired(storedToken)) {
        localStorage.removeItem('access_token');
        setIsInitializing(false);
        return;
      }

      setToken(storedToken);
      try {
        const response = await getCurrentUser();
        setUser(response.data.user);
      } catch {
        localStorage.removeItem('access_token');
        setToken(null);
        setUser(null);
      }

      setIsInitializing(false);
    }

    bootstrap();
    return () => {
    };
  }, []);

  useEffect(() => {
    if (!token) return;

    const payload = decodeJwt(token);
    if (!payload?.exp) return;

    const delay = Math.max(payload.exp * 1000 - Date.now(), 0);
    const timeoutId = window.setTimeout(() => {
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
    }, delay);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [token]);

  async function login(username: string, password: string) {
    const response = await loginRequest({ username, password });
    const accessToken = response.data.access_token;
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
    const currentUser = await getCurrentUser();
    setUser(currentUser.data.user);
  }

  function logout() {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token),
      isInitializing,
      login,
      logout,
    }),
    [user, token, isInitializing],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
