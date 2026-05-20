import { useState, useCallback } from 'react'
import { Upload, Progress, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd/es/upload'
import { initUpload, uploadChunk, completeUpload } from '@/api/upload'

const DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024

interface FileUploadProps {
  projectId: string
  multiple?: boolean
  accept?: string
  onSuccess?: (files: UploadFile[]) => void
}

export default function FileUpload({ projectId, multiple = false, accept, onSuccess }: FileUploadProps) {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const customRequest: UploadProps['customRequest'] = useCallback(
    async ({ file, onProgress, onError, onSuccess: onOk }) => {
      const f = file as File
      setUploading(true)
      setProgress(0)

      try {
        const totalChunks = Math.ceil(f.size / DEFAULT_CHUNK_SIZE)
        const session = await initUpload(projectId, {
          filename: f.name,
          total_size: f.size,
          total_chunks: totalChunks,
          dataset_name: f.name,
        })

        const uploadId = session.upload_id!
        const chunkSize = session.chunk_size || DEFAULT_CHUNK_SIZE

        for (let i = 0; i < totalChunks; i++) {
          const start = i * chunkSize
          const end = Math.min(start + chunkSize, f.size)
          const chunk = f.slice(start, end)
          await uploadChunk(projectId, uploadId, i, totalChunks, chunk)
          const percent = Math.round(((i + 1) / totalChunks) * 100)
          setProgress(percent)
          onProgress?.({ percent })
        }

        await completeUpload(projectId, uploadId, {
          total_chunks: totalChunks,
          dataset_name: f.name,
        })

        message.success(`${f.name} 上传成功`)
        onOk?.(null)
      } catch (err) {
        message.error(`${f.name} 上传失败`)
        onError?.(err as Error)
      } finally {
        setUploading(false)
      }
    },
    [projectId],
  )

  const handleChange: UploadProps['onChange'] = useCallback(
    (info) => {
      setFileList(info.fileList)
      if (info.file.status === 'done' && onSuccess) {
        onSuccess(info.fileList)
      }
    },
    [onSuccess],
  )

  return (
    <div>
      <Upload.Dragger
        name="file"
        multiple={multiple}
        accept={accept}
        fileList={fileList}
        customRequest={customRequest}
        onChange={handleChange}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p>点击或拖拽文件到此处上传</p>
        <p style={{ fontSize: 12, color: '#999' }}>
          支持分片上传，单文件最大无限制（推荐小于 2GB）
        </p>
      </Upload.Dragger>
      {uploading && (
        <Progress percent={progress} status="active" style={{ marginTop: 16 }} />
      )}
    </div>
  )
}
