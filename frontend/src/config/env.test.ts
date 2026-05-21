import { describe, expect, it } from 'vitest';
import { buildTrainingWebSocketUrl, getApiBaseUrl, getWsBaseUrl, shouldEnableMsw } from './env';

describe('frontend environment config', () => {
  it('uses /api/v1 as the default API base URL', () => {
    expect(getApiBaseUrl({})).toBe('/api/v1');
  });

  it('uses VITE_API_BASE_URL when provided', () => {
    expect(getApiBaseUrl({ VITE_API_BASE_URL: 'http://localhost:8000/api/v1' })).toBe(
      'http://localhost:8000/api/v1',
    );
  });

  it('enables MSW in dev unless VITE_ENABLE_MSW is false', () => {
    expect(shouldEnableMsw({ DEV: true })).toBe(true);
    expect(shouldEnableMsw({ DEV: true, VITE_ENABLE_MSW: 'false' })).toBe(false);
    expect(shouldEnableMsw({ DEV: false, VITE_ENABLE_MSW: 'true' })).toBe(false);
  });

  it('derives WS base from relative API base via dev-server host', () => {
    expect(getWsBaseUrl({}, { host: '127.0.0.1:5173', protocol: 'http:' })).toBe(
      'ws://127.0.0.1:5173/api/v1',
    );
  });

  it('derives WS base from absolute API base URL', () => {
    expect(
      getWsBaseUrl({ VITE_API_BASE_URL: 'http://localhost:8000/api/v1' }),
    ).toBe('ws://localhost:8000/api/v1');
    expect(
      getWsBaseUrl({ VITE_API_BASE_URL: 'https://api.example.com/api/v1' }),
    ).toBe('wss://api.example.com/api/v1');
  });

  it('builds training websocket URL with token query', () => {
    expect(
      buildTrainingWebSocketUrl('job-1', {
        env: { VITE_API_BASE_URL: 'http://localhost:8000/api/v1' },
        token: 'abc',
      }),
    ).toBe('ws://localhost:8000/api/v1/ws/training/job-1?token=abc');
  });
});
