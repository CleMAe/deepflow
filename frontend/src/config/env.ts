type FrontendEnv = {
  DEV?: boolean;
  VITE_API_BASE_URL?: string;
  VITE_ENABLE_MSW?: string;
};

export function getApiBaseUrl(env: FrontendEnv = import.meta.env): string {
  return env.VITE_API_BASE_URL?.trim() || '/api/v1';
}

export function shouldEnableMsw(env: FrontendEnv = import.meta.env): boolean {
  return Boolean(env.DEV) && env.VITE_ENABLE_MSW?.toLowerCase() !== 'false';
}

export type BrowserLocation = {
  host: string;
  protocol: 'http:' | 'https:';
};

/** WebSocket base URL aligned with {@link getApiBaseUrl} (scheme/host/path prefix only). */
export function getWsBaseUrl(
  env: FrontendEnv = import.meta.env,
  location?: BrowserLocation,
): string {
  const apiBase = getApiBaseUrl(env).replace(/\/$/, '');

  if (/^https?:\/\//i.test(apiBase)) {
    const parsed = new URL(apiBase);
    const wsScheme = parsed.protocol === 'https:' ? 'wss' : 'ws';
    const pathname = parsed.pathname.replace(/\/$/, '') || '';
    return `${wsScheme}://${parsed.host}${pathname}`;
  }

  const loc =
    location ??
    (typeof window !== 'undefined'
      ? {
          host: window.location.host,
          protocol: window.location.protocol as BrowserLocation['protocol'],
        }
      : { host: 'localhost', protocol: 'http:' as const });

  const wsScheme = loc.protocol === 'https:' ? 'wss' : 'ws';
  const path = apiBase.startsWith('/') ? apiBase : `/${apiBase}`;
  return `${wsScheme}://${loc.host}${path}`;
}

export function buildTrainingWebSocketUrl(
  jobId: string,
  options?: {
    env?: FrontendEnv;
    location?: BrowserLocation;
    token?: string | null;
  },
): string {
  const env = options?.env ?? import.meta.env;
  const token = options?.token ?? null;
  const qs = token ? `?token=${encodeURIComponent(token)}` : '';
  return `${getWsBaseUrl(env, options?.location)}/ws/training/${jobId}${qs}`;
}
