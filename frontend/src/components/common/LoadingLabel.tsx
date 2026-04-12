interface LoadingLabelProps {
  message?: string
}

export function LoadingLabel({ message = 'LOADING_DATA...' }: LoadingLabelProps) {
  return (
    <div className="label" style={{ color: 'var(--primary)', whiteSpace: 'nowrap' }}>
      {message}
      <span style={{ animation: 'blink 0.7s step-end infinite', fontSize: '1.1em' }}>█</span>
    </div>
  )
}
