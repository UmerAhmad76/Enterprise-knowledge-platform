import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { fetchMe, login } from '../api/client.js';
import { USE_DEMO } from '../lib/config.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Token sirf memory mein: localStorage XSS se chori ho sakta hai, isliye wahan nahi rakhte
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);

  const signIn = useCallback(async (tenantSlug, email) => {
    if (USE_DEMO) {
      setToken('demo-token');
      setUser({ user_id: 'demo', tenant_id: 'demo', email, group_ids: [] });
      return;
    }
    const tokenRes = await login(tenantSlug, email);
    // /me ko token seedha pass karte hain, kyunke state abhi set nahi hui hogi
    const me = await fetchMe(tokenRes.access_token);
    setToken(tokenRes.access_token);
    setUser(me);
  }, []);

  const signOut = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ token, user, signIn, signOut }), [token, user, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}