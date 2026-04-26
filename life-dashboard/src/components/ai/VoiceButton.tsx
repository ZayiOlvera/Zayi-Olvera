'use client'

import { useState, useRef } from 'react'

interface VoiceButtonProps {
  onTranscript: (text: string) => void
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyRecognition = any

export function VoiceButton({ onTranscript }: VoiceButtonProps) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<AnyRecognition>(null)

  function startListening() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any
    const SpeechRecognitionAPI = w.SpeechRecognition || w.webkitSpeechRecognition

    if (!SpeechRecognitionAPI) {
      alert('Tu navegador no soporta reconocimiento de voz. Prueba Chrome.')
      return
    }

    const recognition: AnyRecognition = new SpeechRecognitionAPI()
    recognition.lang = 'es-MX'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event: AnyRecognition) => {
      const transcript = event.results[0][0].transcript as string
      onTranscript(transcript)
    }

    recognition.onerror = () => {
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stopListening() {
    recognitionRef.current?.stop()
    setListening(false)
  }

  return (
    <button
      type="button"
      onClick={listening ? stopListening : startListening}
      className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all flex-shrink-0 ${
        listening
          ? 'bg-red-600 hover:bg-red-500 animate-pulse'
          : 'bg-zinc-700 hover:bg-zinc-600'
      }`}
      title={listening ? 'Detener grabación' : 'Hablar'}
    >
      🎤
    </button>
  )
}
