import { useState, useCallback, useRef, useEffect } from 'react'
import { streamChat } from '../lib/sse'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface UIAction {
  action: string
  params: Record<string, string>
}

export function useChat(onUIAction?: (action: UIAction) => void) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [status, setStatus] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    fetch('/api/sessions', { method: 'POST' })
      .then(r => r.json())
      .then(s => setSessionId(s.id))
      .catch(() => {})
  }, [])

  const send = useCallback(async (text: string) => {
    if (!sessionId || streaming) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setStreaming(true)
    setStreamingText('')
    setStatus('CONNECTING')

    const abort = new AbortController()
    abortRef.current = abort

    let accumulated = ''
    try {
      for await (const event of streamChat(sessionId, text, abort.signal)) {
        if (event.event === 'text_delta') {
          accumulated += event.data.content as string
          setStreamingText(accumulated)
          setStatus('STREAMING')
        } else if (event.event === 'tool_call') {
          const toolName = (event.data.tool as string || '').split('__').pop() || 'tool'
          setStatus(toolName.toUpperCase())
        } else if (event.event === 'session_init') {
          setStatus('THINKING')
        } else if (event.event === 'ui_action' && onUIAction) {
          onUIAction(event.data as unknown as UIAction)
          setStatus('UPDATING_VIEW')
        } else if (event.event === 'result') {
          setStatus('DONE')
        } else if (event.event === 'done') {
          break
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        accumulated += '\n\n[Connection error]'
        setStatus('ERROR')
      }
    }

    if (accumulated) {
      setMessages(prev => [...prev, { role: 'assistant', content: accumulated }])
    }
    setStreamingText('')
    setStreaming(false)
    setStatus('')
  }, [sessionId, streaming, onUIAction])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, streaming, streamingText, status, send, cancel, sessionId }
}
