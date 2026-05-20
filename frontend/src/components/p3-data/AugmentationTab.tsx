import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Checkbox,
  Descriptions,
  Input,
  InputNumber,
  Select,
  Slider,
  Space,
  Typography,
  message,
} from 'antd'
import { listDatasets, type Dataset } from '@/api/datasets'
import { augmentDataset, type AugmentRequest, type AugmentResult, type AugmentTransform } from '@/api/cleaningEda'

const { Text, Paragraph } = Typography

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
  const [lastResult, setLastResult] = useState<AugmentResult | null>(null)

  const datasetsQuery = useQuery({
    queryKey: ['datasets', projectId, 'augment'],
    queryFn: () => listDatasets(projectId, { page: 1, page_size: 100 }),
    enabled: !!projectId,
  })

  const imageOptions = useMemo(() => {
    const items = datasetsQuery.data?.items ?? []
    return items
      .filter((d: Dataset) => d.format === 'image')
      .map((d: Dataset) => ({ value: d.id!, label: `${d.name ?? d.id}（图像）` }))
  }, [datasetsQuery.data?.items])

  const allOptions = useMemo(
    () =>
      (datasetsQuery.data?.items ?? []).map((d: Dataset) => ({
        value: d.id!,
        label: `${d.name ?? d.id} (${d.format ?? '?'})`,
      })),
    [datasetsQuery.data?.items],
  )

  const augmentMut = useMutation({
    mutationFn: (body: AugmentRequest) => augmentDataset(projectId, datasetId!, body),
    onSuccess: (data) => {
      setLastResult(data)
      message.success('数据增强任务已提交（Mock）')
      void queryClient.invalidateQueries({ queryKey: ['datasets', projectId] })
    },
    onError: () => message.error('请求失败'),
  })

  const buildTransforms = (): AugmentTransform[] => {
    const t = intensity
    return selectedTypes.map((type) => {
      switch (type) {
        case 'rotate':
          return { type, params: { angle: Math.round(5 + t * 25) } }
        case 'color_jitter':
          return { type, params: { brightness: 0.1 + t * 0.25, contrast: 0.1 + t * 0.2, saturation: 0.1 + t * 0.3 } }
        case 'mixup':
          return { type, params: { alpha: 0.15 + t * 0.35 } }
        case 'cutmix':
          return { type, params: { alpha: 0.2 + t * 0.4 } }
        case 'gaussian_blur':
          return { type, params: { sigma: 0.5 + t * 1.5 } }
        case 'random_crop':
          return { type, params: { scale: 0.85 + t * 0.1 } }
        default:
          return { type }
      }
    })
  }

  const onSubmit = () => {
    if (!datasetId) {
      message.warning('请选择数据集')
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

  return (
    <div>
      <Paragraph type="secondary">
        配置 CV 数据增强：旋转 / 翻转 / 色彩扰动 / MixUp / CutMix 等；强度由滑块统一调节（Mock 联调）。
      </Paragraph>

      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card title="数据集与输出" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space wrap>
              <Text>图像数据集（推荐）：</Text>
              <Select
                allowClear
                showSearch
                optionFilterProp="label"
                placeholder="选择图像数据集"
                style={{ minWidth: 260 }}
                options={imageOptions}
                value={datasetId}
                onChange={setDatasetId}
              />
            </Space>
            <Space wrap>
              <Text>或全部数据集：</Text>
              <Select
                allowClear
                showSearch
                optionFilterProp="label"
                style={{ minWidth: 260 }}
                options={allOptions}
                value={datasetId}
                onChange={setDatasetId}
              />
            </Space>
            <Space wrap>
              <Text>每图生成副本数：</Text>
              <InputNumber min={1} max={8} value={numAugmented} onChange={(v) => setNumAugmented(Number(v) || 1)} />
            </Space>
            <Space wrap>
              <Text>输出数据集名称：</Text>
              <Input style={{ width: 220 }} value={outputName} onChange={(e) => setOutputName(e.target.value)} />
            </Space>
          </Space>
        </Card>

        <Card title="增强方式（多选）" size="small">
          <Checkbox.Group
            value={selectedTypes}
            onChange={(v) => setSelectedTypes(v as AugmentTransform['type'][])}
            style={{ width: '100%' }}
          >
            <Space wrap>
              {TRANSFORM_TYPES.map((x) => (
                <Checkbox key={x} value={x}>
                  {x}
                </Checkbox>
              ))}
            </Space>
          </Checkbox.Group>
        </Card>

        <Card title="强度" size="small">
          <Slider min={0} max={1} step={0.05} value={intensity} onChange={setIntensity} />
          <Text type="secondary">影响旋转角度、色彩扰动、MixUp/CutMix alpha 等参数</Text>
        </Card>

        <Button type="primary" size="large" onClick={onSubmit} loading={augmentMut.isPending}>
          提交增强配置
        </Button>

        {lastResult ? (
          <Card title="执行结果（Mock）" size="small">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="原始样本数">{lastResult.original_count ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="增强后样本数">{lastResult.augmented_count ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="新数据集 ID">{lastResult.new_dataset_id ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="输出名称">{lastResult.output_dataset_name ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        ) : null}
      </Space>
    </div>
  )
}
