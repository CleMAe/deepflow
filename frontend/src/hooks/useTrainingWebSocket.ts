import { useEffect, useRef, useState } from 'react'
import type { TrainingMetricsPoint } from '@/hooks/useTrainingMetricsMock'

export type TrainingWsMessage = {
  type: string
  data: Record<string, unknown>
}

function metricsFromWsData(data: Record<string, unknown>, step: number, epoch: number): TrainingMetricsPoint {
  const num = (key: string, fallback: number) => {
    const v = data[key]
    return typeof v === 'number' ? v : fallback
  }
  return {
    step,
    epoch,
    train_loss: num('train_loss', 0),
    val_loss: num('val_loss', 0),
    accuracy: num('accuracy', 0),
    learning_rate: num('learning_rate', 0.001),
    gpu_util: num('gpu_util', 0),
    gpu_memory: num('gpu_memory', 0),
    cpu_util: num('cpu_util', 0),
    memory_util: num('memory_util', 0),
    throughput: typeof data.throughput === 'string' ? data.throughput : '-',
    eta: typeof data.eta === 'string' ? data.eta : '-',
  }
}

export function useTrainingWebSocket(
  jobId: string | null,
  enabled: boolean,
  onEvent?: (msg: TrainingWsMessage) => void
) {
  const [history, setHistory] = useState<TrainingMetricsPoint[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [latest, setLatest] = useState<TrainingMetricsPoint | null>(null)
  const [connected, setConnected] = useState(false)
  const [failed, setFailed] = useState(false)
  const stepRef = useRef(0)
  const epochRef = useRef(0)

  useEffect(() => {
    if (!enabled || !jobId) {
      return () => {
        setConnected(false)
        setFailed(false)
      }
    }

    stepRef.current = 0
    epochRef.current = 0

    const token = localStorage.getItem('access_token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const qs = token ? `?token=${encodeURIComponent(token)}` : ''
    const url = `${protocol}//${window.location.host}/api/v1/ws/training/${jobId}${qs}`

    const ws = new WebSocket(url)

    ws.onopen = () => {
      setFailed(false)
      setConnected(true)
      setLogs((prev) => [...prev, `INFO [ws] Connected to ${jobId}`])
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as TrainingWsMessage
        onEvent?.(msg)

        if (msg.type === 'metrics' && msg.data) {
          stepRef.current += 1
          const point = metricsFromWsData(msg.data, stepRef.current, epochRef.current || 1)
          setLatest(point)
          setHistory((prev) => [...prev.slice(-199), point])
        }

        if (msg.type === 'progress' && msg.data) {
          const epoch = typeof msg.data.current_epoch === 'number' ? msg.data.current_epoch : epochRef.current
          epochRef.current = epoch
        }

        if (msg.type === 'log' && msg.data) {
          const line =
            typeof msg.data.message === 'string'
              ? msg.data.message
              : typeof msg.data.line === 'string'
                ? msg.data.line
                : JSON.stringify(msg.data)
          setLogs((prev) => [...prev.slice(-199), line])
        }

        if (msg.type === 'status_change') {
          const status = String(msg.data.status ?? '')
          setLogs((prev) => [...prev.slice(-199), `INFO [ws] status -> ${status}`])
        }
      } catch {
        /* ignore malformed frames */
      }
    }

    ws.onerror = () => {
      setFailed(true)
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
    }

    return () => {
      ws.close()
      setConnected(false)
    }
  }, [enabled, jobId, onEvent])

  return { history, logs, latest, connected, failed }
}
