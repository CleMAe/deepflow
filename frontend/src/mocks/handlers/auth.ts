import { http, HttpResponse } from 'msw'

import { DEMO_USER_ID } from '@/mocks/demoIds'

/** HS256 tokens for `sub` = demo user; signed with `DEFAULT_JWT_SECRET_KEY` in `src/infra/config.py` (long exp). */
const MOCK_ACCESS_JWT =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJ1c2VybmFtZSI6ImRlbW8iLCJyb2xlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc3OTI2NTc4NSwiZXhwIjoyMDk0NjI1Nzg1LCJqdGkiOiIxYTcwNzEwNS00MjI3LTRmMzUtODZkYi0yY2ZiMDI4YzllNzgifQ.8xAPROgfTnxtKqYD4Srz0R9PbJ_WAJZOeSizc7Y3azU'
const MOCK_REFRESH_JWT =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJ0eXBlIjoicmVmcmVzaCIsImlhdCI6MTc3OTI2NTc4NSwiZXhwIjoyMDk0NjI1Nzg1LCJqdGkiOiJmMGFhYjY4My0zOTg1LTQwNDEtOTZmNy1lNTYzZTIzNzJmODUifQ.ZsV4161RmNTtlWVeVFksvWp46F4u66-BnAZXs_uZTDM'

export const authHandlers = [
  http.post('/api/v1/auth/login', async () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        access_token: MOCK_ACCESS_JWT,
        refresh_token: MOCK_REFRESH_JWT,
      },
      request_id: 'mock-req-1',
    })
  }),

  http.post('/api/v1/auth/register', async () => {
    return HttpResponse.json(
      {
        code: 0,
        message: 'success',
        data: {
          id: DEMO_USER_ID,
          username: 'newuser',
          role: 'user',
        },
        request_id: 'mock-req-2',
      },
      { status: 201 }
    )
  }),

  http.post('/api/v1/auth/refresh', async () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        access_token: MOCK_ACCESS_JWT,
        refresh_token: MOCK_REFRESH_JWT,
      },
      request_id: 'mock-req-3',
    })
  }),

  http.get('/api/v1/auth/me', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        id: DEMO_USER_ID,
        username: 'demo',
        role: 'admin',
      },
      request_id: 'mock-req-4',
    })
  }),
]
