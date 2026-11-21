// Vite env variables ek jagah, taake baqi code import.meta.env ko direct na padhe
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const USE_DEMO = import.meta.env.VITE_USE_DEMO !== 'false';
export const MAX_QUESTION_LENGTH = 1000;