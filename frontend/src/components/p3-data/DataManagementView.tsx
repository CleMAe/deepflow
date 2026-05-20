import { useCallback, useMemo, useState } from 'react'
import {
  Button,
  Card,
  Image,
  Modal,
  Select,
  Space,
  Table,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import FileUpload from '@/components/common/FileUpload'
import DataTable from '@/components/common/DataTable'
import {
  getDatasetPreview,
  listDatasetImages,
  listDatasets,
  updateDatasetLabels,
  type Dataset,
  type DatasetPreview,
  type ImageItem,
} from '@/api/datasets'

const { Text } = Typography

interface DataManagementViewProps {
  projectId: string
}

/** 与 MSW `datasets` mock 对齐，用于预览列推断 */
function inferPreviewKind(dataset: Dataset): 'image' | 'tabular' {
  if (dataset.format === 'image') return 'image'
  return 'tabular'
}

export default function DataManagementView({ projectId }: DataManagementViewProps) {
  const queryClient = useQueryClient()
  const [previewOpen, setPreviewOpen] = useState(false)
  const [galleryOpen, setGalleryOpen] = useState(false)
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [galleryPage, setGalleryPage] = useState(1)
  const [galleryPageSize] = useState(12)
  const [localLabels, setLocalLabels] = useState<Record<string, string[]>>({})
  const [savingLabels, setSavingLabels] = useState(false)

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 50 }),
    enabled: !!projectId,
  })

  const imagesQuery = useQuery({
    queryKey: ['dataset-images', projectId, activeDataset?.id, galleryPage, galleryPageSize],
    queryFn: () =>
      listDatasetImages(projectId, activeDataset!.id!, {
        page: galleryPage,
        page_size: galleryPageSize,
      }),
    enabled: !!projectId && !!activeDataset?.id && galleryOpen && activeDataset.format === 'image',
  })

  const openPreview = useCallback(
    async (row: Dataset) => {
      if (!row.id) return
      setActiveDataset(row)
      setPreviewOpen(true)
      setPreviewLoading(true)
      setPreview(null)
      try {
        const data = await getDatasetPreview(projectId, row.id)
        setPreview(data)
      } catch {
        message.error('加载预览失败')
      } finally {
        setPreviewLoading(false)
      }
    },
    [projectId],
  )

  const openGallery = useCallback((row: Dataset) => {
    if (!row.id || row.format !== 'image') {
      message.info('仅图像类数据集支持画廊')
      return
    }
    setActiveDataset(row)
    setGalleryPage(1)
    setLocalLabels({})
    setGalleryOpen(true)
  }, [])

  const previewColumns = useMemo(() => {
    const cols = preview?.columns ?? []
    return cols.map((c) => ({
      title: c,
      dataIndex: c,
      key: c,
      ellipsis: true,
      render: (v: unknown) => (typeof v === 'object' ? JSON.stringify(v) : String(v)),
    }))
  }, [preview])

  const listColumns: ColumnsType<Dataset> = useMemo(
    () => [
      { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
      { title: '格式', dataIndex: 'format', key: 'format', width: 90 },
      {
        title: '样本数',
        dataIndex: 'num_samples',
        key: 'num_samples',
        width: 100,
        render: (v?: number) => (v != null ? v.toLocaleString() : '-'),
      },
      { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
      {
        title: '操作',
        key: 'actions',
        width: 200,
        render: (_, row) => (
          <Space>
            <Button type="link" size="small" onClick={() => openPreview(row)}>
              预览
            </Button>
            <Button type="link" size="small" onClick={() => openGallery(row)} disabled={row.format !== 'image'}>
              画廊
            </Button>
          </Space>
        ),
      },
    ],
    [openPreview, openGallery],
  )

  const handleUploadSuccess = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
  }, [projectId, queryClient])

  const handleSaveLabels = useCallback(async () => {
    if (!activeDataset?.id) return
    const items = Object.entries(localLabels).map(([image_id, labels]) => ({ image_id, labels }))
    if (items.length === 0) {
      message.info('未修改任何标签')
      return
    }
    setSavingLabels(true)
    try {
      await updateDatasetLabels(projectId, activeDataset.id, { items })
      message.success('标签已保存')
      setLocalLabels({})
      await queryClient.invalidateQueries({
        queryKey: ['dataset-images', projectId, activeDataset.id],
      })
    } catch {
      message.error('保存失败')
    } finally {
      setSavingLabels(false)
    }
  }, [activeDataset?.id, localLabels, projectId, queryClient])

  const galleryItems = imagesQuery.data?.items ?? []

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据管理</h2>
      <Card title="数据上传" style={{ marginBottom: 16 }}>
        <FileUpload
          projectId={projectId}
          multiple
          accept=".csv,.json,.jsonl,image/*"
          onSuccess={handleUploadSuccess}
        />
      </Card>
      <Card title="数据集列表">
        <DataTable<Dataset>
          rowKey="id"
          columns={listColumns}
          dataSource={datasetsQuery.data?.items ?? []}
          loading={datasetsQuery.isLoading}
          pagination={false}
        />
      </Card>

      <Modal
        title={
          <Space>
            <span>数据预览</span>
            {activeDataset?.name ? <Text type="secondary">· {activeDataset.name}</Text> : null}
          </Space>
        }
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={null}
        width={880}
        destroyOnClose
      >
        {activeDataset && (
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            {inferPreviewKind(activeDataset) === 'image'
              ? '图像数据集：展示元数据与标签字段预览（Mock）'
              : '表格数据：展示前若干行样例（Mock）'}
          </Text>
        )}
        <Table
          size="small"
          loading={previewLoading}
          rowKey={(_, i) => String(i)}
          columns={previewColumns}
          dataSource={preview?.rows ?? []}
          scroll={{ x: 'max-content' }}
          pagination={false}
        />
      </Modal>

      <Modal
        title={
          <Space>
            <span>图片画廊</span>
            {activeDataset?.name ? <Text type="secondary">· {activeDataset.name}</Text> : null}
          </Space>
        }
        open={galleryOpen}
        onCancel={() => setGalleryOpen(false)}
        width={960}
        destroyOnClose
        footer={
          <Space>
            <Button onClick={() => setGalleryOpen(false)}>关闭</Button>
            <Button type="primary" loading={savingLabels} onClick={() => void handleSaveLabels()}>
              保存标签变更
            </Button>
          </Space>
        }
      >
        <Image.PreviewGroup>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: 16,
            }}
          >
            {galleryItems.map((item: ImageItem) => {
              const id = item.id ?? ''
              const labels = localLabels[id] ?? item.labels ?? []
              return (
                <Card key={id} size="small" cover={<Image alt={item.filename} src={item.thumbnail_path} height={120} />}>
                  <Text ellipsis style={{ fontSize: 12 }}>
                    {item.filename}
                  </Text>
                  <Select
                    mode="tags"
                    style={{ width: '100%', marginTop: 8 }}
                    placeholder="标签"
                    value={labels}
                    onChange={(vals) => setLocalLabels((prev) => ({ ...prev, [id]: vals as string[] }))}
                  />
                </Card>
              )
            })}
          </div>
        </Image.PreviewGroup>
        <Space style={{ marginTop: 16 }}>
          <Button
            disabled={galleryPage <= 1}
            onClick={() => setGalleryPage((p) => Math.max(1, p - 1))}
          >
            上一页
          </Button>
          <Button
            disabled={
              !imagesQuery.data?.total ||
              galleryPage * galleryPageSize >= (imagesQuery.data?.total ?? 0)
            }
            onClick={() => setGalleryPage((p) => p + 1)}
          >
            下一页
          </Button>
          <Text type="secondary">
            第 {galleryPage} 页 · 共 {imagesQuery.data?.total ?? 0} 张（Mock）
          </Text>
        </Space>
      </Modal>
    </div>
  )
}
