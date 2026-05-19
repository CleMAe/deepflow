import { useState, useCallback } from 'react'
import { Upload, Progress, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd/es/upload'

interface FileUploadProps {
  action: string
  multiple?: boolean
  accept?: string
  onSuccess?: (files: UploadFile[]) => void
}

export default function FileUpload({ action, multiple = false, accept, onSuccess }: FileUploadProps) {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)

  const handleChange: UploadProps['onChange'] = useCallback((info) => {
    setFileList(info.fileList)
    if (info.file.status === 'uploading') {
      setUploading(true)
    }
    if (info.file.status === 'done') {
      setUploading(false)
      message.success(`${info.file.name} 上传成功`)
      if (onSuccess) onSuccess(info.fileList)
    }
    if (info.file.status === 'error') {
      setUploading(false)
      message.error(`${info.file.name} 上传失败`)
    }
  }, [onSuccess])

  return (
    <div>
      <Upload.Dragger
        name="file"
        action={action}
        multiple={multiple}
        accept={accept}
        fileList={fileList}
        onChange={handleChange}
        headers={{ Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` }}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p>点击或拖拽文件到此处上传</p>
      </Upload.Dragger>
      {uploading && <Progress percent={50} status="active" style={{ marginTop: 16 }} />}
    </div>
  )
}
