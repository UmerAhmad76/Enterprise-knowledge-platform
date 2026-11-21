import { useAuth } from '../context/AuthContext.jsx';
import { initials } from '../lib/format.js';

// Upar ki patti: brand, aur login hone par user ka avatar aur sign out
export default function Topbar() {
  const { user, signOut } = useAuth();
  return (
    <header className="topbar">
      <div className="brand">
        <div className="logo">E</div>
        <span>EKP Assistant</span>
      </div>
      {user && (
        <div className="user-chip">
          <div className="avatar">{initials(user.email)}</div>
          <span className="email">{user.email}</span>
          <button className="btn btn-ghost btn-sm" onClick={signOut}>
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}