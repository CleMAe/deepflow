import { useCallback, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Image,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { p3UseMock } from '@/config/p3Api'
import { formatApiError } from '@/lib/formatApiError'
import type { ColumnsType } from 'antd/es/table'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import FileUpload from '@/components/common/FileUpload'
import DataTable from '@/components/common/DataTable'
import DatasetEditModal from '@/components/p3-data/DatasetEditModal'
import {
  deleteDataset,
  getDatasetPreview,
  listDatasetImages,
  listDatasets,
  updateDataset,
  updateDatasetLabels,
  type Dataset,
  type DatasetPreview,
  type DatasetUpdate,
  type ImageItem,
} from '@/api/datasets'

const { Text } = Typography

interface DataManagementViewProps {
  projectId: string
}

function inferPreviewKind(dataset: Dataset): 'image' | 'tabular' {
  if (dataset.format === 'image') return 'image'
  return 'tabular'
}

function invalidateAllDatasets(queryClient: ReturnType<typeof useQueryClient>, projectId: string) {
  void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
}

export default function DataManagementView({ projectId }: DataManagementViewProps) {
  const queryClient = useQueryClient()
  const [previewOpen, setPreviewOpen] = useState(false)
  const [galleryOpen, setGalleryOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null)
  const [preview, setPreview] = useState<DatasetPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [galleryPage, setGalleryPage] = useState(1)
  const [galleryPageSize] = useState(12)
  const [galleryLabelFilter, setGalleryLabelFilter] = useState<string>()
  const [localLabels, setLocalLabels] = useState<Record<string, string[]>>({})
  const [savingLabels, setSavingLabels] = useState(false)
  const [search, setSearch] = useState('')
  const [tagFilter, setTagFilter] = useState<string[]>([])

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, search],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 50, search: search || undefined }),
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

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: DatasetUpdate }) => updateDataset(projectId, id, body),
    onSuccess: () => {
      message.success('数据集已更新')
      setEditOpen(false)
      invalidateAllDatasets(queryClient, projectId)
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteDataset(projectId, id),
    onSuccess: () => {
      message.success('数据集已删除')
      invalidateAllDatasets(queryClient, projectId)
    },
    onError: (err) => message.error(formatApiError(err)),
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
      } catch (err) {
        message.error(formatApiError(err, '加载预览失败'))
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
    setGalleryLabelFilter(undefined)
    setLocalLabels({})
    setGalleryOpen(true)
  }, [])

  const openEdit = useCallback((row: Dataset) => {
    setActiveDataset(row)
    setEditOpen(true)
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

  const allTags = useMemo(() => {
    const set = new Set<string>()
    for (const d of datasetsQuery.data?.items ?? []) {
      for (const t of d.tags ?? []) set.add(t)
    }
    return [...set].sort()
  }, [datasetsQuery.data?.items])

  const galleryLabelOptions = useMemo(() => {
    const set = new Set<string>()
    for (const item of imagesQuery.data?.items ?? []) {
      for (const l of item.labels ?? []) set.add(l)
    }
    return [...set].map((l) => ({ value: l, label: l }))
  }, [imagesQuery.data?.items])

  const galleryItems = useMemo(() => {
    const items = imagesQuery.data?.items ?? []
    if (!galleryLabelFilter) return items
    return items.filter((item) => (item.labels ?? []).includes(galleryLabelFilter))
  }, [imagesQuery.data?.items, galleryLabelFilter])

  const filteredItems = useMemo(() => {
    const items = datasetsQuery.data?.items ?? []
    if (!tagFilter.length) return items
    return items.filter((d) => tagFilter.every((t) => (d.tags ?? []).includes(t)))
  }, [datasetsQuery.data?.items, tagFilter])

  const listColumns: ColumnsType<Dataset> = useMemo(
    () => [
      { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
      { title: '格式', dataIndex: 'format', key: 'format', width: 90 },
      {
        title: '标签',
        dataIndex: 'tags',
        key: 'tags',
        width: 160,
        render: (tags?: string[]) =>
          tags?.length ? (
            <Space size={[0, 4]} wrap>
              {tags.map((t) => (
                <Tag key={t}>{t}</Tag>
              ))}
            </Space>
          ) : (
            '-'
          ),
      },
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
        width: 260,
        render: (_, row) => (
          <Space wrap>
            <Button type="link" size="small" onClick={() => openPreview(row)}>
              预览
            </Button>
            <Button type="link" size="small" onClick={() => openGallery(row)} disabled={row.format !== 'image'}>
              画廊
            </Button>
            <Button type="link" size="small" onClick={() => openEdit(row)}>
              编辑
            </Button>
            <Popconfirm
              title="确定删除该数据集？"
              description="删除后不可恢复"
              onConfirm={() => row.id && deleteMut.mutate(row.id)}
            >
              <Button type="link" size="small" danger loading={deleteMut.isPending}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [openPreview, openGallery, openEdit, deleteMut],
  )

  const handleUploadSuccess = useCallback(() => {
    invalidateAllDatasets(queryClient, projectId)
    message.success('上传完成，列表已刷新')
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
    } catch (err) {
      message.error(formatApiError(err, '保存失败'))
    } finally {
      setSavingLabels(false)
    }
  }, [activeDataset, localLabels, projectId, queryClient])

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据管理</h2>
      {!p3UseMock ? (
        <Alert
          type="info"
          showIcon
          closable
          style={{ marginBottom: 16 }}
          message="已连接后端数据 API"
          description="请从工作台进入「Demo Project」；勿使用仅存在于 MSW 的旧 mock 项目名（如「商品图像分类」）。"
        />
      ) : null}
      {datasetsQuery.isError ? (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          message="无法加载数据集列表"
          description={formatApiError(datasetsQuery.error, '请确认已进入 Demo Project 且后端已启动')}
        />
      ) : null}
      <Card title="数据上传" style={{ marginBottom: 16 }}>
        <FileUpload
          projectId={projectId}
          multiple
          accept=".csv,.json,.jsonl,image/*"
          onSuccess={handleUploadSuccess}
        />
      </Card>
      <Card
        title="数据集列表"
        extra={
          <Space wrap>
            <Select
              allowClear
              mode="multiple"
              placeholder="按标签筛选"
              style={{ minWidth: 160 }}
              options={allTags.map((t) => ({ value: t, label: t }))}
              value={tagFilter}
              onChange={setTagFilter}
            />
            <Input.Search
              allowClear
              placeholder="搜索名称（服务端）"
              style={{ width: 200 }}
              onSearch={setSearch}
            />
          </Space>
        }
      >
        <DataTable<Dataset>
          rowKey="id"
          columns={listColumns}
          dataSource={filteredItems}
          loading={datasetsQuery.isLoading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>

      <DatasetEditModal
        open={editOpen}
        dataset={activeDataset}
        loading={updateMut.isPending}
        onCancel={() => setEditOpen(false)}
        onSubmit={(values) => {
          if (!activeDataset?.id) return
          updateMut.mutate({ id: activeDataset.id, body: values })
        }}
      />

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
              ? '图像数据集：展示元数据与标签字段预览'
              : `表格数据：共 ${preview?.total_rows ?? '-'} 行，下方为预览样例`}
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
        <Space style={{ marginBottom: 16 }} wrap>
          <Text>按标签筛选：</Text>
          <Select
            allowClear
            showSearch
            placeholder="选择标签"
            style={{ minWidth: 160 }}
            options={galleryLabelOptions}
            value={galleryLabelFilter}
            onChange={setGalleryLabelFilter}
          />
        </Space>
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
                <Card
                  key={id}
                  size="small"
                  cover={
                    <Image
                      alt={item.filename}
                      src={item.thumbnail_path}
                      height={120}
                      style={{ objectFit: 'cover' }}
                      fallback="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Crect fill='%23f0f0f0' width='120' height='120'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E无预览%3C/text%3E%3C/svg%3E"
                    />
                  }
                >
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
        {!galleryItems.length && !imagesQuery.isLoading ? (
          <Text type="secondary" style={{ display: 'block', marginTop: 12 }}>
            当前筛选无图片
          </Text>
        ) : null}
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
            第 {galleryPage} 页 · 本页显示 {galleryItems.length} 张
            {galleryLabelFilter ? `（已筛选「${galleryLabelFilter}」）` : ''} · 数据集共{' '}
            {imagesQuery.data?.total ?? 0} 张
          </Text>
        </Space>
      </Modal>
    </div>
  )
}
