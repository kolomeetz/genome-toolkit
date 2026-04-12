import { useState, useCallback, useRef, useEffect, useMemo } from 'react'

export type VoiceState = 'idle' | 'recording' | 'loading' | 'speaking'

/** Try backend TTS, return audio URL or null (= use browser fallback). */
async function fetchBackendTTS(text: string, emotion?: string): Promise<string | null> {
  try {
    const resp = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, emotion: emotion || '' }),
    })
    // 204 = browser mode, no audio from backend
    if (resp.status === 204) return null
    if (!resp.ok) return null
    const blob = await resp.blob()
    if (blob.size === 0) return null
    return URL.createObjectURL(blob)
  } catch {
    return null
  }
}

export function useVoice() {
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [loading, setLoading] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const recordingStartRef = useRef<number>(0)

  // Check browser support for STT
  const supported = typeof window !== 'undefined' && (
    'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
  )

  // Derived state machine
  const state: VoiceState = useMemo(() => {
    if (speaking) return 'speaking'
    if (loading) return 'loading'
    if (listening) return 'recording'
    return 'idle'
  }, [listening, speaking, loading])

  // Recording timer
  useEffect(() => {
    if (listening) {
      recordingStartRef.current = Date.now()
      setRecordingTime(0)
      timerRef.current = setInterval(() => {
        setRecordingTime((Date.now() - recordingStartRef.current) / 1000)
      }, 100)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      setRecordingTime(0)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [listening])

  const speak = useCallback(async (text: string, emotion?: string) => {
    if (!voiceEnabled || !text) return

    // Stop any current playback
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    window.speechSynthesis.cancel()

    setLoading(true)

    // Try backend TTS first
    const audioUrl = await fetchBackendTTS(text, emotion)

    if (audioUrl) {
      // Play backend audio
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      audio.onplay = () => { setLoading(false); setSpeaking(true) }
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(audioUrl) }
      audio.onerror = () => { setSpeaking(false); setLoading(false); URL.revokeObjectURL(audioUrl) }
      audio.play().catch(() => { setLoading(false) })
    } else {
      // Fallback to browser SpeechSynthesis
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.95
      utterance.pitch = 1.0

      const voices = window.speechSynthesis.getVoices()
      const preferred = voices.find(v =>
        v.name.includes('Samantha') || v.name.includes('Karen') ||
        v.name.includes('Google') || v.name.includes('Natural')
      ) || voices.find(v => v.lang.startsWith('en'))
      if (preferred) utterance.voice = preferred

      utterance.onstart = () => { setLoading(false); setSpeaking(true) }
      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => { setSpeaking(false); setLoading(false) }

      synthRef.current = utterance
      window.speechSynthesis.speak(utterance)
    }
  }, [voiceEnabled])

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    window.speechSynthesis.cancel()
    setSpeaking(false)
    setLoading(false)
  }, [])

  const startListening = useCallback((onResult: (text: string) => void) => {
    if (!supported || listening) return

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    let handled = false

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      if (handled) return
      const result = event.results[event.results.length - 1]
      if (!result.isFinal) return
      handled = true
      const text = result[0].transcript
      setListening(false)
      recognition.stop()
      onResult(text)
    }

    recognition.onerror = () => { setListening(false); handled = true }
    recognition.onend = () => setListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }, [supported, listening])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setListening(false)
  }, [])

  const toggleVoice = useCallback(() => {
    if (voiceEnabled) {
      stopSpeaking()
      stopListening()
    }
    setVoiceEnabled(prev => !prev)
  }, [voiceEnabled, stopSpeaking, stopListening])

  // Load browser voices (some browsers load async)
  useEffect(() => {
    window.speechSynthesis?.getVoices()
    window.speechSynthesis?.addEventListener('voiceschanged', () => {
      window.speechSynthesis.getVoices()
    })
  }, [])

  return {
    voiceEnabled,
    listening,
    speaking,
    supported,
    state,
    recordingTime,
    toggleVoice,
    speak,
    stopSpeaking,
    startListening,
    stopListening,
  }
}
