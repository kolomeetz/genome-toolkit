import type { Category, ActionType } from '../../types/genomics'

const CATEGORIES: { key: Category; label: string }[] = [
  { key: 'mood', label: 'Mood' },
  { key: 'stress', label: 'Stress' },
  { key: 'sleep', label: 'Sleep' },
  { key: 'focus', label: 'Focus' },
]

const ACTION_TYPES: { key: ActionType; label: string }[] = [
  { key: 'consider', label: 'Consider' },
  { key: 'monitor', label: 'Monitor' },
  { key: 'discuss', label: 'Discuss' },
  { key: 'try', label: 'Try' },
]

interface FilterBarProps {
  activeCategory: Category | null
  activeActionType: ActionType | null
  onCategoryChange: (cat: Category) => void
  onActionTypeChange: (type: ActionType) => void
  onClearAll: () => void
  onExport: (format: 'pdf' | 'md' | 'doctor') => void
}

const chipStyle = (active: boolean) => ({
  fontFamily: 'var(--font-mono)',
  fontSize: 'var(--font-size-xs)',
  fontWeight: active ? 600 : 500,
  textTransform: 'uppercase' as const,
  letterSpacing: '0.1em',
  padding: '4px 10px',
  border: `1px solid ${active ? 'var(--primary)' : 'var(--border)'}`,
  background: 'transparent',
  color: active ? 'var(--primary)' : 'var(--text-secondary)',
  cursor: 'pointer',
})

const exportStyle = (accent: boolean) => ({
  fontFamily: 'var(--font-mono)',
  fontSize: 'var(--font-size-xs)',
  fontWeight: 500,
  textTransform: 'uppercase' as const,
  letterSpacing: '0.1em',
  padding: '4px 10px',
  border: `1px solid ${accent ? 'var(--accent)' : 'var(--border-strong)'}`,
  background: 'transparent',
  color: accent ? 'var(--accent)' : 'var(--text-secondary)',
  cursor: 'pointer',
})

export function FilterBar({ activeCategory, activeActionType, onCategoryChange, onActionTypeChange, onClearAll, onExport }: FilterBarProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 24px', borderBottom: '1px dashed var(--border-dashed)' }}>
      <div style={{ display: 'flex', gap: 6 }}>
        <button style={chipStyle(activeCategory === null && activeActionType === null)} onClick={onClearAll}>All</button>
        {CATEGORIES.map(c => (
          <button key={c.key} style={chipStyle(activeCategory === c.key)} onClick={() => onCategoryChange(c.key)}>{c.label}</button>
        ))}
        <span style={{ width: 1, background: 'var(--border)', margin: '0 6px' }} />
        {ACTION_TYPES.map(t => (
          <button key={t.key} style={chipStyle(activeActionType === t.key)} onClick={() => onActionTypeChange(t.key)}>{t.label}</button>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        <button style={exportStyle(false)} onClick={() => onExport('pdf')}>Export PDF</button>
        <button style={exportStyle(false)} onClick={() => onExport('md')}>Export MD</button>
        <button style={exportStyle(true)} onClick={() => onExport('doctor')}>Print for doctor</button>
      </div>
    </div>
  )
}
