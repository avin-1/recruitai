const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1']);

const isBrowser = () => typeof window !== 'undefined';

const isLocalhost = () => isBrowser() && LOCAL_HOSTS.has(window.location.hostname);

const buildBase = (envValue, localPort, remoteBasePath = '/api') => {
  if (envValue) {
    return envValue;
  }

  if (isLocalhost()) {
    return `http://localhost:${localPort}${remoteBasePath}`;
  }

  return remoteBasePath;
};

export const SHORTLISTING_API_BASE = buildBase(
  import.meta.env.VITE_SHORTLISTING_API_URL,
  5001
);

export const INTERVIEW_API_BASE = buildBase(
  import.meta.env.VITE_API_BASE_URL,
  5002
);

export const CORE_API_BASE = buildBase(
  import.meta.env.VITE_CORE_API_BASE_URL,
  8080,
  ''
);

export const SETTINGS_API_BASE = buildBase(
  import.meta.env.VITE_SETTINGS_API_URL,
  5003,
  '/api/settings'
);

