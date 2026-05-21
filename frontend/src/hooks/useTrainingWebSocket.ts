import { useEffect, useRef, useState } from 'react'
import type { TrainingJob } from '@/api/training'
import { getTrainingLogs } from '@/api/training'
import type { TrainingMetricsPoint } from './useTrainingMetricsMock'

interface WsMessage {
  type: 'metrics' | 'progress' | 'status_change'
  data: Record<string, unknown>
}

export function useTrainingWebSocket(
  projectId: string,
  job: TrainingJob | null,
  enabled: boolean
) {
  const jobId = job?.id
  const isRunning = enabled && job?.status === 'running'

  const [history, setHistory] = useState<TrainingMetricsPoint[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [latest, setLatest] = useState<TrainingMetricsPoint | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const stepRef = useRef(0)

  // Poll logs via REST API (backend WS does not push logs)
  useEffect(() => {
    if (!isRunning || !jobId) return

    let cancelled = false
    const poll = async () => {
      try {
        const data = await getTrainingLogs(projectId, jobId, 100)
        if (!cancelled) setLogs(data.logs ?? [])
      } catch {
        // ignore
      }
    }

    poll()
    const interval = window.setInterval(poll, 3000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [isRunning, jobId, projectId])

  // Reset state when job stops or is not selected
  useEffect(() => {
    if (isRunning && jobId) return
    const id = window.setTimeout(() => {
      setHistory([])
      setLatest(null)
      setConnected(false)
    }, 0)
    return () => window.clearTimeout(id)
  }, [isRunning, jobId])

  // WebSocket connection
  useEffect(() => {
    if (!isRunning || !jobId) return

    const token = localStorage.getItem('access_token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/training/${jobId}?token=${token ?? ''}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      stepRef.current = (job?.current_epoch ?? 0) * 50
      setLogs((prev) => [
        ...prev,
        `INFO [ws] Connected to training job ${jobId}`,
      ])
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage
        if (msg.type === 'metrics') {
          stepRef.current += 1
          const epoch = Math.floor(stepRef.current / 50) + 1
          const point: TrainingMetricsPoint = {
            step: stepRef.current,
            epoch,
            train_loss: Number(msg.data.train_loss ?? 0),
            val_loss: Number(msg.data.val_loss ?? 0),
            accuracy: Number(msg.data.accuracy ?? 0),
            learning_rate: Number(msg.data.learning_rate ?? 0),
            // Backend WS currently does not push resource utilisation
            gpu_util: 0,
            gpu_memory: 0,
            cpu_util: 0,
            memory_util: 0,
            throughput: '-',
            eta: '-',
          }
          setLatest(point)
          setHistory((prev) => [...prev.slice(-199), point])
          setLogs((prev) => [
            ...prev.slice(-99),
            `INFO Epoch ${epoch} step ${point.step} — train_loss=${point.train_loss.toFixed(4)} val_loss=${point.val_loss.toFixed(4)} acc=${point.accuracy.toFixed(4)}`,
          ])
        } else if (msg.type === 'status_change') {
          setLogs((prev) => [
            ...prev.slice(-99),
            `INFO Status changed to ${String(msg.data.status)}`,
          ])
        } else if (msg.type === 'progress') {
          const current = msg.data.current_epoch as number | undefined
          const total = msg.data.total_epochs as number | undefined
          if (current !== undefined && total !== undefined) {
            setLogs((prev) => [
              ...prev.slice(-99),
              `INFO Progress ${current}/${total} epochs`,
            ])
          }
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [isRunning, jobId, job?.current_epoch])

  return {
    history: isRunning ? history : [],
    logs: isRunning ? logs : [],
    latest: isRunning ? latest : null,
    connected,
  }
}
