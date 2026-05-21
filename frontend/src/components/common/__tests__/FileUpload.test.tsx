import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as uploadApi from '@/api/upload'
import FileUpload from '../FileUpload'

const mockMessageSuccess = vi.hoisted(() => vi.fn())
const mockMessageError = vi.hoisted(() => vi.fn())

vi.mock('@/api/upload', () => ({
  initUpload: vi.fn(),
  uploadChunk: vi.fn(),
  completeUpload: vi.fn(),
}))

vi.mock('antd', async (importOriginal) => {
  const mod = await importOriginal<typeof import('antd')>()
  return {
    ...mod,
    message: {
      ...mod.message,
      success: mockMessageSuccess,
      error: mockMessageError,
    },
  }
})

const PROJECT_ID = '11111111-1111-1111-1111-111111111111'

function createCsvFile(name = 'test.csv', content = 'age,bmi,risk_label\n1,22,0') {
  return new File([content], name, { type: 'text/csv' })
}

function getFileInput(container: HTMLElement): HTMLInputElement {
  const input = container.querySelector('input[type="file"]')
  if (!input) {
    throw new Error('File input not found inside Upload.Dragger')
  }
  return input as HTMLInputElement
}

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(uploadApi.initUpload).mockResolvedValue({
      upload_id: 'upload-session-001',
      chunk_size: 5 * 1024 * 1024,
      received_chunks: [],
    } as Awaited<ReturnType<typeof uploadApi.initUpload>>)
    vi.mocked(uploadApi.uploadChunk).mockResolvedValue({ received_chunks: [0] })
    vi.mocked(uploadApi.completeUpload).mockResolvedValue({
      id: 'dataset-001',
      name: 'test.csv',
    } as Awaited<ReturnType<typeof uploadApi.completeUpload>>)
  })

  it('renders upload area hint text', () => {
    render(<FileUpload projectId={PROJECT_ID} />)

    expect(screen.getByText('点击或拖拽文件到此处上传')).toBeInTheDocument()
    expect(
      screen.getByText('支持分片上传，单文件最大无限制（推荐小于 2GB）'),
    ).toBeInTheDocument()
  })

  it('calls upload APIs and onSuccess when a file is selected via userEvent', async () => {
    const onSuccess = vi.fn()
    const user = userEvent.setup()
    const file = createCsvFile()

    const { container } = render(
      <FileUpload projectId={PROJECT_ID} accept=".csv" onSuccess={onSuccess} />,
    )

    await user.upload(getFileInput(container), file)

    await waitFor(() => {
      expect(uploadApi.initUpload).toHaveBeenCalledWith(
        PROJECT_ID,
        expect.objectContaining({
          filename: 'test.csv',
          dataset_name: 'test.csv',
        }),
      )
    })

    await waitFor(() => {
      expect(uploadApi.uploadChunk).toHaveBeenCalled()
      expect(uploadApi.completeUpload).toHaveBeenCalledWith(
        PROJECT_ID,
        'upload-session-001',
        expect.objectContaining({ dataset_name: 'test.csv' }),
      )
    })

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled()
      const fileList = onSuccess.mock.calls[0][0]
      expect(fileList.length).toBeGreaterThanOrEqual(1)
      expect(fileList[0].name).toBe('test.csv')
    })

    expect(mockMessageSuccess).toHaveBeenCalledWith('test.csv 上传成功')
    expect(uploadApi.initUpload).toHaveBeenCalledTimes(1)
  })

  it('triggers upload flow via fireEvent.change with a mock file', async () => {
    const onSuccess = vi.fn()
    const file = createCsvFile('mock-data.csv')

    const { container } = render(
      <FileUpload projectId={PROJECT_ID} onSuccess={onSuccess} />,
    )

    fireEvent.change(getFileInput(container), { target: { files: [file] } })

    await waitFor(() => {
      expect(uploadApi.initUpload).toHaveBeenCalled()
    })

    await waitFor(
      () => {
        expect(onSuccess).toHaveBeenCalled()
      },
      { timeout: 5000 },
    )
  })
})
