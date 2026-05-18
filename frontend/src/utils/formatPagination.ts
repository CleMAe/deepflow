/**
 * Shared pagination helper — covered by unit tests; P2 may relocate.
 */

export interface PaginationInput {
  page: number;
  pageSize: number;
  total: number;
}

export interface PaginationMeta extends PaginationInput {
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export function formatPagination({
  page,
  pageSize,
  total,
}: PaginationInput): PaginationMeta {
  const safePageSize = Math.max(1, pageSize);
  const totalPages = Math.max(1, Math.ceil(total / safePageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);

  return {
    page: safePage,
    pageSize: safePageSize,
    total,
    totalPages,
    hasNext: safePage < totalPages,
    hasPrev: safePage > 1,
  };
}
