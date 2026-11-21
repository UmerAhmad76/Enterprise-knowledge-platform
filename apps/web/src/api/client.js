import { API_BASE } from '../lib/config.js';

// Error ke saath HTTP status bhi rakhte hain, taake UI 401 aur 403 ko alag handle kar sake
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Ek hi function sab API calls ke liye: auth header, JSON, aur error handling
export async function apiRequest(path, { method = 'GET', token, body } = {}) {
  const headers = { 'Content-Type': 'application/json' };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;

  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'Network error');
  }

  let data = null;

  try {
    data = await response.json();
  } catch {
    // Body khaali ya JSON nahi hai, data null rehne do
  }

  if (!response.ok) {
    const detail =
      data && typeof data.detail === 'string'
        ? data.detail
        : `Request failed (${response.status})`;

    throw new ApiError(response.status, detail);
  }

  return data;
}

export function login(tenantSlug, email) {
  return apiRequest('/auth/dev-token', {
    method: 'POST',
    body: {
      tenant_slug: tenantSlug,
      email,
    },
  });
}

export function fetchMe(token) {
  return apiRequest('/me', {
    token,
  });
}

export function askQuestion(token, question, topK = 8) {
  return apiRequest('/chat', {
    method: 'POST',
    token,
    body: {
      question,
      top_k: topK,
    },
  });
}

// Status code ko user ki samajh mein aane wale message mein badalta hai
export function friendlyError(err) {
  switch (err.status) {
    case 0:
      return 'Cannot reach the server. Is the backend running?';

    case 401:
      return 'Your session has expired. Please sign in again.';

    case 403:
      return 'Your account is inactive. Contact your administrator.';

    case 404:
      return 'Workspace or user not found.';

    case 422:
      return 'Please check your input and try again.';

    default:
      return err.message || 'Something went wrong.';
  }
}

export function sendFeedback(token, queryId, rating, comment) {
  return apiRequest('/feedback', {
    method: 'POST',
    token,
    body: {
      query_id: queryId,
      rating,
      comment: comment || null,
    },
  });
}
