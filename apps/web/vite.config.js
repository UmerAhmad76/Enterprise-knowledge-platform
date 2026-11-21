import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite React plugin JSX ko compile karta hai, dev server port 5173 par chalta hai
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});