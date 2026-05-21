import { useEffect } from 'react'
import { Form, Input, Modal, Select } from 'antd'
import type { Dataset, DatasetUpdate } from '@/api/datasets'

interface DatasetEditModalProps {
  open: boolean
  dataset: Dataset | null
  loading?: boolean
  onCancel: () => void
  onSubmit: (values: DatasetUpdate) => void
}

export default function DatasetEditModal({
  open,
  dataset,
  loading,
  onCancel,
  onSubmit,
}: DatasetEditModalProps) {
  const [form] = Form.useForm<DatasetUpdate>()

  useEffect(() => {
    if (open && dataset) {
      form.setFieldsValue({
        name: dataset.name,
        tags: dataset.tags ?? [],
      })
    }
  }, [open, dataset, form])

  return (
    <Modal
      title="编辑数据集"
      open={open}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical" onFinish={onSubmit}>
        <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="tags" label="标签">
          <Select mode="tags" placeholder="输入标签后回车" tokenSeparators={[',']} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
