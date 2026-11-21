import { useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import { friendlyError, sendFeedback } from '../api/client.js';

const MAX_COMMENT = 500;

// Thumbs up/down. 👎 par optional comment box khulta hai. Demo jawab par network call nahi hoti.
export default function FeedbackBar({ queryId }) {
  const { token, signOut } = useAuth();
  const [rating, setRating] = useState(null);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [commentSaved, setCommentSaved] = useState(false);
  const [error, setError] = useState('');

  async function vote(value, text) {
    if (String(queryId).startsWith('demo')) {
      setRating(value);
      if (text) setCommentSaved(true);
      return;
    }
    setSaving(true);
    setError('');
    try {
      await sendFeedback(token, queryId, value, text);
      setRating(value);
      if (text) setCommentSaved(true);
    } catch (err) {
      if (err.status === 401) {
        signOut();
        return;
      }
      setError(friendlyError(err));
    } finally {
      setSaving(false);
    }
  }

  function handleVote(value) {
    if (saving || rating === value) return;
    vote(value, null);
  }

  function sendComment() {
    const text = comment.trim();
    if (!text || rating !== -1) return;
    vote(-1, text);
  }

  let thanks = null;
  if (rating === 1) thanks = 'Thanks for the feedback.';
  if (commentSaved) thanks = 'Thanks, your comment was saved.';

  return (
    <div className="feedback">
      <div className="feedback-row">
        <span>Was this helpful?</span>
        <button
          type="button"
          className="vote"
          aria-pressed={rating === 1}
          aria-label="Helpful"
          disabled={saving}
          onClick={() => handleVote(1)}
        >
          👍
        </button>
        <button
          type="button"
          className="vote"
          aria-pressed={rating === -1}
          aria-label="Not helpful"
          disabled={saving}
          onClick={() => handleVote(-1)}
        >
          👎
        </button>
        {thanks && <span>{thanks}</span>}
      </div>

      {rating === -1 && !commentSaved && (
        <div className="comment-box">
          <textarea
            rows={2}
            maxLength={MAX_COMMENT}
            placeholder="What was wrong? (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <button
            className="btn btn-ghost btn-sm"
            type="button"
            disabled={saving || !comment.trim()}
            onClick={sendComment}
          >
            Send comment
          </button>
        </div>
      )}

      {error && (
        <div className="feedback-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}