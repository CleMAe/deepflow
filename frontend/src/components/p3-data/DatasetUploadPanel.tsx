import { useCallback, useState } from 'react'
import { Alert, Progress, Typography, Upload, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd/es/upload'
import { useQueryClient } from '@tanstack/react-query'
import {
  completeDatasetUpload,
  initDatasetUpload,
  uploadDatasetChunk,
} from '@/api/datasets'
import {
  UPLOAD_CHUNK_STRATEGY_HINT,
  buildUploadChunkPlan,
  detectDatasetFileFormat,
} from '@/components/p3-data/uploadChunkPlan'

const { Dragger } = Upload
const { Text } = Typography

interface DatasetUploadPanelProps {
  projectId: string
}

export default function DatasetUploadPanel({ projectId }: DatasetUploadPanelProps) {
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)
  const [percent, setPercent] = useState(0)
  const [statusText, setStatusText] = useState('')

  const uploadFile = useCallback(
    async (file: File) => {
      const previewPlan = buildUploadChunkPlan(file)

      setUploading(true)
      setPercent(0)
      setStatusText(`正在初始化上传（${previewPlan.strategyLabel}）…`)

      try {
        const session = await initDatasetUpload(projectId, {
          filename: file.name,
          total_size: file.size,
          total_chunks: previewPlan.totalChunks,
          dataset_name: file.name.replace(/\.[^.]+$/, ''),
          format: previewPlan.format,
        })

        const uploadId = session?.upload_id
        if (!uploadId) {
          throw new Error('未获取到 upload_id')
        }

        const plan = buildUploadChunkPlan(file, session.chunk_size)
        const { chunks, totalChunks } = plan

        setStatusText(`开始上传：${plan.strategyLabel}`)

        for (let index = 0; index < chunks.length; index += 1) {
          const formData = new FormData()
          formData.append('chunk', chunks[index], `${file.name}.part${index}`)
          formData.append('chunk_index', String(index))
          formData.append('total_chunks', String(totalChunks))

          await uploadDatasetChunk(projectId, uploadId, formData)
          const nextPercent = Math.round(((index + 1) / totalChunks) * 90)
          setPercent(nextPercent)
          setStatusText(
            `[${detectDatasetFileFormat(file).toUpperCase()}] 分片 ${index + 1}/${totalChunks} · ${plan.strategyLabel}`,
          )
        }

        setStatusText('正在合并分片…')
        await completeDatasetUpload(projectId, uploadId, {
          total_chunks: totalChunks,
          dataset_name: file.name.replace(/\.[^.]+$/, ''),
        })

        setPercent(100)
        setStatusText(`上传完成（${plan.strategyLabel}）`)
        message.success(`${file.name} 上传成功`)
        await queryClient.invalidateQueries({ queryKey: ['p3-datasets', projectId] })
      } catch {
        message.error(`${file.name} 上传失败`)
        throw new Error('upload failed')
      } finally {
        setUploading(false)
      }
    },
    [projectId, queryClient],
  )

  const customRequest: UploadProps['customRequest'] = async (options) => {
    const file = options.file as File
    try {
      await uploadFile(file)
      options.onSuccess?.({}, new XMLHttpRequest())
    } catch (error) {
      options.onError?.(error as Error)
    }
  }

  return (
    <div>
      <Alert
        type="info"
        showIcon
        message="分片上传（Mock · 按类型自适应）"
        description={`Day1 模拟 init → chunk → complete。${UPLOAD_CHUNK_STRATEGY_HINT}`}
        style={{ marginBottom: 16 }}
      />
      <Dragger
        multiple
        disabled={uploading}
        showUploadList={false}
        accept=".csv,.json,.jsonl,image/*"
        customRequest={customRequest}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
        <p className="ant-upload-hint">{UPLOAD_CHUNK_STRATEGY_HINT} 上传完成后自动刷新数据集列表。</p>
      </Dragger>
      {uploading && (
        <div style={{ marginTop: 16 }}>
          <Progress percent={percent} status="active" />
          <Text type="secondary">{statusText}</Text>
        </div>
      )}
    </div>
  )
}
