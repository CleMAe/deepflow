import { describe, expect, it } from 'vitest';

import { formatPagination } from './formatPagination';

describe('formatPagination', () => {
  it('computes page metadata', () => {
    expect(formatPagination({ page: 2, pageSize: 10, total: 25 })).toEqual({
      page: 2,
      pageSize: 10,
      total: 25,
      totalPages: 3,
      hasNext: true,
      hasPrev: true,
    });
  });

  it('clamps invalid page numbers', () => {
    expect(formatPagination({ page: 99, pageSize: 10, total: 5 }).page).toBe(1);
  });
});
