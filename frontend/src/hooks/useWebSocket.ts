import { useEffect, useRef } from 'react'
import { createWebSocketClient } from '@/services/websocketClient'
import { useMetricsStore } from '@/store/metricsStore'
import type { RealtimeMetrics } from '@/types'

export function useWebSocket() {
  const updateFromWebSocket = useMetricsStore((s) => s.updateFromWebSocket)
  const clientRef = useRef<ReturnType<typeof createWebSocketClient> | null>(null)

  useEffect(() => {
    const client = createWebSocketClient((data) => {
      updateFromWebSocket(data as RealtimeMetrics)
    })
    clientRef.current = client
    client.connect()

    return () => {
      client.disconnect()
    }
  }, [updateFromWebSocket])
}
