import { useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import { friendlyError } from '../api/client.js';

// Dev login form. Production mein ye SSO button se badal jayega.
export default function LoginForm() {
  const { signIn } = useAuth();
  const [tenant, setTenant] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    if (!tenant.trim() || !email.trim()) {
      setError('Workspace and email are required.');
      return;
    }
    setBusy(true);
    try {
      await signIn(tenant.trim(), email.trim());
    } catch (err) {
      setError(friendlyError(err));
      setBusy(false);
    }
  }

  return (
    <form className="card login-card" onSubmit={handleSubmit} noValidate>
      <h2>Sign in</h2>
      <p className="sub">Use your workspace and work email.</p>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      <div className="field">
        <label htmlFor="tenant">Workspace</label>
        <input
          id="tenant"
          placeholder="acme"
          autoComplete="organization"
          value={tenant}
          onChange={(e) => setTenant(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="email">Work email</label>
        <input
          id="email"
          type="email"
          placeholder="alice@acme.test"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
        {busy ? 'Please wait…' : 'Continue'}
      </button>
      <p className="hint">Development sign-in. Production will use your company SSO.</p>
    </form>
  );
}