import { useState } from 'react';
import { MAX_QUESTION_LENGTH } from '../lib/config.js';

// Input box: Enter se bhejo, Shift+Enter se nayi line, aur character count
export default function Composer({ onSend, disabled }) {
  const [value, setValue] = useState('');

  function submit() {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue('');
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="composer">
      <div className="composer-box">
        <textarea
          rows={1}
          maxLength={MAX_QUESTION_LENGTH}
          placeholder="Ask about your documents…"
          aria-label="Your question"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className="btn btn-primary send"
          type="button"
          aria-label="Send"
          onClick={submit}
          disabled={disabled || !value.trim()}
        >
          ➤
        </button>
      </div>
      <div className="count">
        {value.length}/{MAX_QUESTION_LENGTH}
      </div>
    </div>
  );
}