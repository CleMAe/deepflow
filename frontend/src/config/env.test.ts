import { describe, expect, it } from 'vitest';
import { getApiBaseUrl, shouldEnableMsw } from './env';

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
});
