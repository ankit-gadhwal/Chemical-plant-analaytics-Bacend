/**
 * Configuration & Constants
 * Chemical Plant Equipment Analytics
 */

// ---------------------------------------------------------------------------
// Resolve the backend API base URL at runtime.
//
// Priority order:
//  1. `REACT_APP_API_URL` injected via meta tag (set in Vercel env vars) — see index.html
//  2. Same origin when the frontend is served directly by FastAPI (port 8000 / prod)
//  3. Localhost fallback for local development without Docker
// ---------------------------------------------------------------------------
function resolveApiBaseUrl() {
  // Check for a meta tag injected at build/deploy time (Vercel)
  const metaTag = document.querySelector('meta[name="api-base-url"]');
  if (metaTag && metaTag.content && metaTag.content !== '__API_BASE_URL__') {
    return metaTag.content.replace(/\/$/, ''); // strip trailing slash
  }
  // If running on port 8000 (local FastAPI) or a standard HTTP/HTTPS port, use same origin
  const port = window.location.port;
  if (port === '8000' || port === '80' || port === '443' || port === '') {
    return window.location.origin;
  }
  // Local dev fallback
  return 'http://localhost:8000';
}

export const CONFIG = {
  API_BASE_URL: resolveApiBaseUrl(),

  STORAGE_KEYS: {
    ACCESS_TOKEN: 'chempulse_access_token',
    REFRESH_TOKEN: 'chempulse_refresh_token',
    USER: 'chempulse_user',
    ACTIVE_DATASET_UID: 'chempulse_active_dataset_uid',
    ACTIVE_CHAT_SESSION: 'chempulse_active_chat_session',
  },

  ENDPOINTS: {
    // Auth
    LOGIN: '/auth/login',
    SIGNUP: '/auth/signup',
    REFRESH_TOKEN: '/auth/refresh_token',
    LOGOUT: '/auth/logout',

    // Datasets
    DATASETS: '/dataset/',
    DATASET_UPLOAD: '/dataset/upload',
    DATASET_DETAIL: (uid) => `/dataset/${uid}`,

    // Equipment
    EQUIPMENT: '/equipment/',
    EQUIPMENT_DETAIL: (uid) => `/equipment/${uid}`,
    EQUIPMENT_BY_DATASET: (datasetUid) => `/equipment/dataset/${datasetUid}`,

    // Documents
    DOCUMENTS_UPLOAD: '/documents/upload',
    DOCUMENTS_BY_DATASET: (datasetUid) => `/documents/dataset/${datasetUid}`,
    DOCUMENT_DETAIL: (docUid) => `/documents/${docUid}`,

    // Chat / AI
    CHAT_SQL: '/chat/sql',
    CHAT_RAG: '/chat/rag',
    CHAT_SESSIONS: '/chat/sessions',
    CHAT_SESSION_DETAIL: (sessionUid) => `/chat/sessions/${sessionUid}`,
  },

  EQUIPMENT_TYPES: [
    'Pump',
    'Heat Exchanger',
    'Reactor',
    'Column',
    'Compressor',
    'Storage Tank',
    'Valve'
  ]
};
