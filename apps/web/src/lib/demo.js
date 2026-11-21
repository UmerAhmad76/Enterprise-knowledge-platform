// Backend /chat ready hone se pehle layout test karne ke liye fake jawab. query_id hai taake feedback UI bhi dikhe.
export function demoAnswer(question) {
  return {
    query_id: 'demo-query',
    answer:
      `Preview answer for: "${question}". The /chat endpoint is not connected yet, ` +
      'so this text only shows the layout [1].',
    citations: [
      { number: 1, document_id: 'demo', chunk_id: 'demo', title: 'Sample policy document' },
    ],
    invalid_citation_numbers: [],
    model_name: 'demo',
    prompt_version: '-',
    demo: true,
  };
}