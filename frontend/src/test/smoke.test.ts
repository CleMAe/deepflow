/**
 * Vitest smoke test — validates test runner wiring before P2 scaffold lands.
 */

describe('vitest scaffold', () => {
  it('runs assertions', () => {
    expect(1 + 1).toBe(2);
  });

  it('supports DOM environment', () => {
    const el = document.createElement('div');
    el.textContent = 'DeepFlow';
    expect(el.textContent).toBe('DeepFlow');
  });
});
