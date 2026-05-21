import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Image,
  Input,
  InputNumber,
  Row,
  Select,
  Slider,
  Space,
  Typography,
  message,
} from 'antd'
import { listDatasetImages, listDatasets, type Dataset } from '@/api/datasets'
import {
  augmentDataset,
  splitDataset,
  type AugmentRequest,
  type AugmentResult,
  type AugmentTransform,
  type SplitRequest,
  type SplitResult,
} from '@/api/cleaningEda'
import { buildAugmentPreviewStyle } from '@/components/p3-data/augmentPreviewStyle'
import { datasetOptionLabel, isImageDataset } from '@/components/p3-data/datasetFormat'
import { formatApiError } from '@/lib/formatApiError'

const { Text, Paragraph, Title } = Typography

const TRANSFORM_TYPES: AugmentTransform['type'][] = [
  'rotate',
  'flip_horizontal',
  'flip_vertical',
  'color_jitter',
  'random_crop',
  'mixup',
  'cutmix',
  'gaussian_blur',
]

interface AugmentationTabProps {
  projectId: string
}

export default function AugmentationTab({ projectId }: AugmentationTabProps) {
  const queryClient = useQueryClient()
  const [datasetId, setDatasetId] = useState<string>()
  const [selectedTypes, setSelectedTypes] = useState<AugmentTransform['type'][]>([
    'rotate',
    'flip_horizontal',
    'color_jitter',
  ])
  const [intensity, setIntensity] = useState(0.5)
  const [numAugmented, setNumAugmented] = useState(1)
  const [outputName, setOutputName] = useState('aug_train_v1')
  const [lastAugment, setLastAugment] = useState<AugmentResult | null>(null)
  const [lastSplit, setLastSplit] = useState<SplitResult | null>(null)
  const [trainRatio, setTrainRatio] = useState(0.7)
  const [valRatio, setValRatio] = useState(0.15)

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, 'augment'],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 100 }),
    enabled: !!projectId,
  })

  const imageOptions = useMemo(() => {
    const items = datasetsQuery.data?.items ?? []
    return items.filter(isImageDataset).map((d: Dataset) => ({
      value: d.id!,
      label: datasetOptionLabel(d),
    }))
  }, [datasetsQuery.data?.items])

  const allOptions = useMemo(
    () => (datasetsQuery.data?.items ?? []).map((d: Dataset) => ({ value: d.id!, label: datasetOptionLabel(d) })),
    [datasetsQuery.data?.items],
  )

  const selectedDataset = (datasetsQuery.data?.items ?? []).find((d) => d.id === datasetId)

  const previewImageQuery = useQuery({
    queryKey: ['aug-preview-src', projectId, datasetId],
    queryFn: () => listDatasetImages(projectId, datasetId!, { page: 1, page_size: 1 }),
    enabled: !!projectId && !!datasetId && isImageDataset(selectedDataset),
  })

  const compareQuery = useQuery({
    queryKey: ['aug-compare', projectId, datasetId, lastAugment?.new_dataset_id],
    queryFn: async () => {
      const orig = await listDatasetImages(projectId, datasetId!, { page: 1, page_size: 1 })
      const aug = await listDatasetImages(projectId, lastAugment!.new_dataset_id!, { page: 1, page_size: 1 })
      return { orig: orig.items?.[0], aug: aug.items?.[0] }
    },
    enabled: !!projectId && !!datasetId && !!lastAugment?.new_dataset_id,
  })

  const buildTransforms = (): AugmentTransform[] => {
    const t = intensity
    return selectedTypes.map((type) => {
      switch (type) {
        case 'rotate':
          return { type, params: { angle: Math.round(5 + t * 25) } }
        case 'color_jitter':
          return {
            type,
            params: { brightness: 0.1 + t * 0.25, contrast: 0.1 + t * 0.2, saturation: 0.1 + t * 0.3 },
          }
        case 'mixup':
          return { type, params: { alpha: 0.15 + t * 0.35 } }
        case 'cutmix':
          return { type, params: { alpha: 0.2 + t * 0.4 } }
        case 'gaussian_blur':
          return { type, params: { radius: 0.5 + t * 1.5 } }
        case 'random_crop':
          return { type, params: { ratio: 0.85 + t * 0.1 } }
        default:
          return { type }
      }
    })
  }

  const previewStyle = useMemo(() => buildAugmentPreviewStyle(buildTransforms(), intensity), [selectedTypes, intensity])

  const previewSrc = previewImageQuery.data?.items?.[0]?.thumbnail_path

  const augmentMut = useMutation({
    mutationFn: (body: AugmentRequest) => augmentDataset(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastAugment(data)
      message.success('数据增强已完成')
      void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const splitMut = useMutation({
    mutationFn: (body: SplitRequest) => splitDataset(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastSplit(data)
      message.success('数据集划分完成')
      void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
    },
    onError: (err) => message.error(formatApiError(err)),
  })

  const requireDataset = () => {
    if (!datasetId) {
      message.warning('请选择数据集')
      return false
    }
    return true
  }

  const onAugment = () => {
    if (!requireDataset()) return
    if (!isImageDataset(selectedDataset)) {
      message.warning('数据增强仅支持图像数据集')
      return
    }
    if (!selectedTypes.length) {
      message.warning('请至少选择一种增强方式')
      return
    }
    augmentMut.mutate({
      transforms: buildTransforms(),
      num_augmented: numAugmented,
      output_dataset_name: outputName || undefined,
    })
  }

  const onSplit = () => {
    if (!requireDataset()) return
    const test = Math.max(0, 1 - trainRatio - valRatio)
    if (trainRatio + valRatio + test < 0.99 || trainRatio + valRatio + test > 1.01) {
      message.warning('train + val + test 比例之和须为 1')
      return
    }
    const body: SplitRequest = {
      ratios: { train: trainRatio, val: valRatio, test },
      random_seed: 42,
    }
    splitMut.mutate(body)
  }

  if (datasetsQuery.isError) {
    return (
      <Alert
        type="error"
        showIcon
        message="无法加载数据集"
        description={formatApiError(datasetsQuery.error, '请从工作台进入 Demo Project')}
      />
    )
  }

  return (
    <div>
      <Paragraph type="secondary">
        图像增强（Pillow）与 train/val/test 划分；下方提供提交前 CSS 近似预览与提交后抽样对比。
      </Paragraph>

      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card title="数据集" size="small">
          <Select
            allowClear
            showSearch
            optionFilterProp="label"
            placeholder="选择图像数据集（增强 / 预览）"
            style={{ minWidth: 320 }}
            options={imageOptions}
            value={datasetId}
            onChange={(v) => {
              setDatasetId(v)
              setLastAugment(null)
            }}
            loading={datasetsQuery.isLoading}
          />
          <div style={{ marginTop: 12 }}>
            <Text type="secondary">划分可使用任意数据集：</Text>
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder="选择数据集（划分）"
              style={{ minWidth: 320, marginLeft: 8 }}
              options={allOptions}
              value={datasetId}
              onChange={setDatasetId}
            />
          </div>
        </Card>

        <Card title="增强预览对比（提交前）" size="small">
          {!datasetId || !isImageDataset(selectedDataset) ? (
            <Text type="secondary">请选择图像数据集后查看原图与参数预览</Text>
          ) : !previewSrc ? (
            <Text type="secondary">加载样例图…</Text>
          ) : (
            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Title level={5}>原图</Title>
                <Image src={previewSrc} alt="original" style={{ maxHeight: 220, objectFit: 'contain' }} />
              </Col>
              <Col xs={24} md={12}>
                <Title level={5}>预览效果（CSS 近似）</Title>
                <Image
                  src={previewSrc}
                  alt="augmented preview"
                  style={{ maxHeight: 220, objectFit: 'contain', ...previewStyle }}
                />
                <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                  已选：{selectedTypes.join(', ') || '无'}
                </Text>
              </Col>
            </Row>
          )}
        </Card>

        <Card title="CV 数据增强" size="small">
          <Checkbox.Group
            value={selectedTypes}
            onChange={(v) => setSelectedTypes(v as AugmentTransform['type'][])}
            style={{ width: '100%', marginBottom: 12 }}
          >
            <Space wrap>
              {TRANSFORM_TYPES.map((x) => (
                <Checkbox key={x} value={x}>
                  {x}
                </Checkbox>
              ))}
            </Space>
          </Checkbox.Group>
          <Space wrap style={{ marginBottom: 12 }}>
            <Text>每图副本数：</Text>
            <InputNumber min={1} max={8} value={numAugmented} onChange={(v) => setNumAugmented(Number(v) || 1)} />
            <Text>输出名称：</Text>
            <Input style={{ width: 200 }} value={outputName} onChange={(e) => setOutputName(e.target.value)} />
          </Space>
          <Slider min={0} max={1} step={0.05} value={intensity} onChange={setIntensity} />
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            强度影响旋转、色彩扰动、MixUp/CutMix 等参数
          </Text>
          <Button type="primary" onClick={onAugment} loading={augmentMut.isPending} disabled={!imageOptions.length}>
            提交增强
          </Button>
          {!imageOptions.length ? (
            <Alert type="warning" showIcon style={{ marginTop: 12 }} message="当前项目暂无图像数据集" />
          ) : null}
        </Card>

        {lastAugment?.new_dataset_id ? (
          <Card title="增强结果对比（提交后抽样）" size="small" loading={compareQuery.isLoading}>
            {compareQuery.data?.orig && compareQuery.data?.aug ? (
              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Text type="secondary">源数据集</Text>
                  <Image
                    src={compareQuery.data.orig.thumbnail_path}
                    alt="before"
                    style={{ maxHeight: 200, marginTop: 8 }}
                  />
                </Col>
                <Col xs={24} md={12}>
                  <Text type="secondary">增强后 · {lastAugment.output_dataset_name}</Text>
                  <Image
                    src={compareQuery.data.aug.thumbnail_path}
                    alt="after"
                    style={{ maxHeight: 200, marginTop: 8 }}
                  />
                </Col>
              </Row>
            ) : (
              <Text type="secondary">增强完成，新数据集 ID：{lastAugment.new_dataset_id}</Text>
            )}
            <Descriptions column={2} size="small" bordered style={{ marginTop: 16 }}>
              <Descriptions.Item label="原始样本数">{lastAugment.original_count ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="增强后样本数">{lastAugment.augmented_count ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        ) : null}

        <Card title="数据集划分 (train / val / test)" size="small">
          <Space wrap style={{ marginBottom: 12 }}>
            <Text>train</Text>
            <InputNumber min={0.01} max={0.99} step={0.05} value={trainRatio} onChange={(v) => setTrainRatio(Number(v) || 0.7)} />
            <Text>val</Text>
            <InputNumber min={0} max={0.99} step={0.05} value={valRatio} onChange={(v) => setValRatio(Number(v) || 0)} />
            <Text>test（自动）</Text>
            <Text type="secondary">{(1 - trainRatio - valRatio).toFixed(2)}</Text>
          </Space>
          <Button onClick={onSplit} loading={splitMut.isPending}>
            执行划分
          </Button>
        </Card>

        {lastSplit ? (
          <Card title="划分结果" size="small">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="train">{lastSplit.train_count} · {lastSplit.train_dataset_id}</Descriptions.Item>
              <Descriptions.Item label="val">{lastSplit.val_count} · {lastSplit.val_dataset_id ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="test">{lastSplit.test_count} · {lastSplit.test_dataset_id ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        ) : null}
      </Space>
    </div>
  )
}
