import { useAuth } from './context/AuthContext.jsx';
import Topbar from './components/Topbar.jsx';
import LoginPage from './components/LoginPage.jsx';
import ChatPage from './components/ChatPage.jsx';

// Agar user login hai to chat dikhao, warna hero aur login form
export default function App() {
  const { user } = useAuth();
  return (
    <div className="app-shell">
      <Topbar />
      {user ? <ChatPage /> : <LoginPage />}
    </div>
  );
}