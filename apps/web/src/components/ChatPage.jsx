import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import { askQuestion, friendlyError } from '../api/client.js';
import { demoAnswer } from '../lib/demo.js';
import { USE_DEMO } from '../lib/config.js';
import Message from './Message.jsx';
import Composer from './Composer.jsx';

const SUGGESTIONS = [
  'What is our annual leave policy?',
  'Summarise the onboarding process.',
  'Who should I contact about salary reviews?',
];

// Chat screen: messages ki list, typing indicator, aur neeche composer
export default function ChatPage() {
  const { token, signOut } = useAuth();
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const logRef = useRef(null);
  const nextId = useRef(1);

  // Naya message aaye to neeche scroll karo
  useEffect(() => {
    const log = logRef.current;
    if (log) log.scrollTop = log.scrollHeight;
  }, [messages, busy]);

  async function send(question) {
    const text = question.trim();
    if (!text || busy) return;

    setMessages((list) => [...list, { id: nextId.current++, role: 'user', text }]);
    setBusy(true);
    try {
      const data = USE_DEMO ? demoAnswer(text) : await askQuestion(token, text);
      setMessages((list) => [...list, { id: nextId.current++, role: 'bot', data }]);
    } catch (err) {
      // Token expire ho gaya: user ko login par bhejo
      if (err.status === 401) {
        signOut();
        return;
      }
      setMessages((list) => [
        ...list,
        { id: nextId.current++, role: 'bot', error: friendlyError(err) },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="chat">
      <div className="chat-log" ref={logRef}>
        {messages.length === 0 ? (
          <Welcome onPick={send} />
        ) : (
          messages.map((msg) => <Message key={msg.id} msg={msg} />)
        )}
        {busy && <Typing />}
      </div>
      <Composer onSend={send} disabled={busy} />
    </main>
  );
}

function Welcome({ onPick }) {
  return (
    <div className="welcome">
      <h2>How can I help you today?</h2>
      <p>Ask a question about your documents. Answers include citations.</p>
      <div className="chips">
        {SUGGESTIONS.map((q) => (
          <button key={q} className="chip" type="button" onClick={() => onPick(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function Typing() {
  return (
    <div className="msg bot">
      <div className="bot-card">
        <div className="typing" aria-label="Assistant is typing">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}