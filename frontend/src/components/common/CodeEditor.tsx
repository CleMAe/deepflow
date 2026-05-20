import { useRef, useMemo } from 'react'
import { Button } from 'antd'

interface CodeEditorProps {
  value: string
  onChange?: (value: string) => void
  language?: string
  height?: string
  readOnly?: boolean
}

export default function CodeEditor({
  value,
  onChange,
  language = 'json',
  height = '300px',
  readOnly = false,
}: CodeEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const lineNoRef = useRef<HTMLDivElement>(null)

  const lines = value.split('\n')

  const error = useMemo(() => {
    if (language === 'json' && value.trim()) {
      try {
        JSON.parse(value)
        return null
      } catch (e) {
        return (e as Error).message
      }
    }
    return null
  }, [language, value])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange?.(e.target.value)
  }

  const handleScroll = () => {
    if (lineNoRef.current && textareaRef.current) {
      lineNoRef.current.scrollTop = textareaRef.current.scrollTop
    }
  }

  const handleFormat = () => {
    if (language !== 'json') return
    try {
      const formatted = JSON.stringify(JSON.parse(value), null, 2)
      onChange?.(formatted)
    } catch {
      // ignore format on invalid json
    }
  }

  const handleMinify = () => {
    if (language !== 'json') return
    try {
      const minified = JSON.stringify(JSON.parse(value))
      onChange?.(minified)
    } catch {
      // ignore minify on invalid json
    }
  }

  return (
    <div style={{ width: '100%' }}>
      {language === 'json' && !readOnly && (
        <div style={{ marginBottom: 8, display: 'flex', gap: 8 }}>
          <Button size="small" onClick={handleFormat}>格式化</Button>
          <Button size="small" onClick={handleMinify}>压缩</Button>
        </div>
      )}
      <div
        style={{
          display: 'flex',
          border: `1px solid ${error ? '#ff4d4f' : '#d9d9d9'}`,
          borderRadius: 6,
          overflow: 'hidden',
          fontFamily: 'monospace',
          fontSize: 13,
          lineHeight: '20px',
          height,
        }}
      >
        <div
          ref={lineNoRef}
          style={{
            width: 40,
            background: '#f5f5f5',
            color: '#999',
            textAlign: 'right',
            padding: '8px 6px',
            overflow: 'hidden',
            overflowY: 'hidden',
            userSelect: 'none',
            flexShrink: 0,
          }}
        >
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onScroll={handleScroll}
          readOnly={readOnly}
          spellCheck={false}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            padding: '8px 12px',
            resize: 'none',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            lineHeight: 'inherit',
            whiteSpace: 'pre',
            overflow: 'auto',
            background: '#fff',
            color: '#333',
          }}
        />
      </div>
      {error && (
        <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 4 }}>{error}</div>
      )}
    </div>
  )
}
