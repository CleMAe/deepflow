import { useEffect, useRef, useState } from 'react'
import type { TrainingJob } from '@/api/training'

export interface TrainingMetricsPoint {
  step: number
  epoch: number
  train_loss: number
  val_loss: number
  accuracy: number
  learning_rate: number
  gpu_util: number
  gpu_memory: number
  cpu_util: number
  memory_util: number
  throughput: string
  eta: string
}

function nextMetrics(step: number, epoch: number): TrainingMetricsPoint {
  const decay = Math.exp(-step / 80)
  return {
    step,
    epoch,
    train_loss: Number((0.8 * decay + 0.05 + Math.random() * 0.02).toFixed(4)),
    val_loss: Number((0.95 * decay + 0.08 + Math.random() * 0.03).toFixed(4)),
    accuracy: Number(Math.min(0.99, 0.55 + (1 - decay) * 0.4 + Math.random() * 0.02).toFixed(4)),
    learning_rate: Number((0.001 * decay + 0.0001).toFixed(6)),
    gpu_util: Math.round(70 + Math.random() * 25),
    gpu_memory: Math.round(60 + Math.random() * 30),
    cpu_util: Math.round(30 + Math.random() * 40),
    memory_util: Math.round(45 + Math.random() * 35),
    throughput: `${Math.round(90 + Math.random() * 60)} samples/s`,
    eta: `${Math.max(1, Math.round((50 - step) * 1.2))}m ${Math.round(Math.random() * 59)}s`,
  }
}

export function useTrainingMetricsMock(job: TrainingJob | null, enabled: boolean) {
  const jobId = job?.id
  const isRunning = enabled && job?.status === 'running'
  const [history, setHistory] = useState<TrainingMetricsPoint[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [latest, setLatest] = useState<TrainingMetricsPoint | null>(null)
  const stepRef = useRef(0)

  useEffect(() => {
    if (!isRunning || !jobId) {
      return
    }

    stepRef.current = job?.current_epoch ? job.current_epoch * 50 : 0

    const pushTick = (isFirst: boolean) => {
      if (isFirst) {
        setHistory([])
        setLatest(null)
        setLogs([
          `INFO [mock-ws] Connected to training job ${jobId}`,
          `INFO [mock-ws] Streaming metrics for ${job?.name ?? jobId}`,
        ])
        return
      }
      stepRef.current += 1
      const epoch = Math.floor(stepRef.current / 50) + 1
      const point = nextMetrics(stepRef.current, epoch)
      setLatest(point)
      setHistory((prev) => [...prev.slice(-199), point])
      setLogs((prev) => [
        ...prev.slice(-99),
        `INFO Epoch ${epoch} step ${point.step} — train_loss=${point.train_loss} val_loss=${point.val_loss} acc=${point.accuracy}`,
      ])
    }

    const firstTimer = window.setTimeout(() => pushTick(true), 0)
    const timer = window.setInterval(() => pushTick(false), 1500)

    return () => {
      window.clearTimeout(firstTimer)
      window.clearInterval(timer)
    }
  }, [isRunning, jobId, job?.name, job?.current_epoch])

  return { history: isRunning ? history : [], logs: isRunning ? logs : [], latest: isRunning ? latest : null }
}
