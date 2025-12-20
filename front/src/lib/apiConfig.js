const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1']);

const isBrowser = () => typeof window !== 'undefined';

const isLocalhost = () => isBrowser() && LOCAL_HOSTS.has(window.location.hostname);

const buildBase = (envValue, localPort, remoteBasePath = '/api') => {
  let base = '';
  if (envValue) {
    base = envValue;
  } else if (isLocalhost()) {
    base = `http://localhost:${localPort}`;
  } else {
    // If not localhost (e.g. ngrok), use relative path
    // This allows the frontend to work on any domain
    return remoteBasePath || '';
  }

  // Ensure base doesn't end with slash to avoid double slashes
  if (base.endsWith('/')) {
    base = base.slice(0, -1);
  }

  // If base is just the domain (no path), append remoteBasePath
  // But we need to be careful not to append if it's already there.
  // A simple heuristic: if base doesn't contain '/api' and remoteBasePath starts with '/api', append it.
  // However, for CORE_API_BASE, remoteBasePath is empty.

  if (remoteBasePath && !base.includes(remoteBasePath) && base.startsWith('http')) {
    return `${base}${remoteBasePath}`;
  }

  return base;
};

export const SHORTLISTING_API_BASE = buildBase(
  import.meta.env.VITE_SHORTLISTING_URL || import.meta.env.VITE_SHORTLISTING_API_URL,
  5001,
  '/api'
);

export const INTERVIEW_API_BASE = buildBase(
  import.meta.env.VITE_INTERVIEW_URL || import.meta.env.VITE_INTERVIEW_API_URL,
  5002,
  '/api'
);

export const CORE_API_BASE = buildBase(
  import.meta.env.VITE_API_URL || import.meta.env.VITE_CORE_API_BASE_URL,
  8080,
  ''
);

export const SETTINGS_API_BASE = buildBase(
  import.meta.env.VITE_SHORTLISTING_URL || import.meta.env.VITE_SHORTLISTING_API_URL,
  5001,
  '/api'
);

export const NOTIFICATION_API_BASE = buildBase(
  import.meta.env.VITE_NOTIFICATION_URL || import.meta.env.VITE_NOTIFICATION_API_URL,
  5005,
  ''
);

