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
