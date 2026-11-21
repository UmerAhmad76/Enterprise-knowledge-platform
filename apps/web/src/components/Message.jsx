import FeedbackBar from './FeedbackBar.jsx';

// Ek message: user ka sawal ya assistant ka jawab, citations, meta pills, aur feedback
export default function Message({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="msg user">
        <div className="bubble-user">{msg.text}</div>
      </div>
    );
  }

  if (msg.error) {
    return (
      <div className="msg bot">
        <div className="bot-card">
          <p className="answer">{msg.error}</p>
        </div>
      </div>
    );
  }

  const { data } = msg;
  const hasInvalidCitations = data.invalid_citation_numbers?.length > 0;

  return (
    <div className="msg bot">
      <div className="bot-card">
        <p className="answer">{data.answer}</p>

        {data.citations?.length > 0 && (
          <div className="cites">
            {data.citations.map((c) => (
              <span className="cite" key={c.number} title={`Document: ${c.document_id}`}>
                <b>{c.number}</b>
                {c.title}
              </span>
            ))}
          </div>
        )}

        <div className="meta">
          {data.demo && <span className="pill demo">Demo mode</span>}
          {hasInvalidCitations && (
            <span className="pill warn">Some citations could not be verified</span>
          )}
          {data.model_name && <span className="pill">Model: {data.model_name}</span>}
          {data.prompt_version && <span className="pill">Prompt: {data.prompt_version}</span>}
        </div>

        {data.query_id && <FeedbackBar queryId={data.query_id} />}
      </div>
    </div>
  );
}