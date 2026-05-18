import { http, HttpResponse } from 'msw'

export const authHandlers = [
  http.post('/api/v1/auth/login', async () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
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
          id: 'mock-user-id',
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
        access_token: 'mock_refreshed_token',
        refresh_token: 'mock_refreshed_refresh',
      },
      request_id: 'mock-req-3',
    })
  }),

  http.get('/api/v1/auth/me', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: {
        id: 'mock-user-id',
        username: 'demo',
        role: 'admin',
      },
      request_id: 'mock-req-4',
    })
  }),
]
