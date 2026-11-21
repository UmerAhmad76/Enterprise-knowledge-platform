import LoginForm from './LoginForm.jsx';

const FEATURES = [
  {
    title: 'Access-aware search',
    text: 'Every result is filtered by your workspace, team and permissions before it reaches the screen.',
  },
  {
    title: 'Cited answers',
    text: 'Each claim links back to its source document so you can verify it yourself.',
  },
  {
    title: 'Hybrid retrieval',
    text: 'Keyword precision combined with semantic understanding for better recall.',
  },
];

// Hero section: gradient background, headline, feature cards, aur login form
export default function LoginPage() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <span className="badge">● Secure · Permission-aware · Cited answers</span>
          <h1>Find answers in your company's documents, in seconds.</h1>
          <p className="lead">
            Ask in plain language. Get a clear answer with sources, and only from the documents
            your role is allowed to see.
          </p>
          <div className="features">
            {FEATURES.map((f) => (
              <div className="feature" key={f.title}>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <div className="login-wrap">
        <LoginForm />
      </div>
    </>
  );
}