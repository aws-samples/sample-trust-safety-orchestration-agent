type MessageHandler = (data: unknown) => void

const WS_URL = import.meta.env.VITE_WS_URL || ''

export function createWebSocketClient(onMessage: MessageHandler) {
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectDelay = 1000

  function connect() {
    if (!WS_URL) return

    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      reconnectDelay = 1000
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch {
        // ignore non-JSON messages
      }
    }

    ws.onclose = () => {
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      reconnectDelay = Math.min(reconnectDelay * 2, 30000)
      connect()
    }, reconnectDelay)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
  }

  return { connect, disconnect }
}
