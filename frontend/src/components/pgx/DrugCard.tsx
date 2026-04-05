import type { DrugCardData } from '../../types/pgx'

const IMPACT_STYLES: Record<string, { borderColor: string; statusColor: string; bg?: string }> = {
  ok: { borderColor: 'var(--sig-benefit)', statusColor: 'var(--sig-benefit)' },
  adjust: { borderColor: 'var(--sig-reduced)', statusColor: 'var(--sig-reduced)' },
  warn: { borderColor: 'var(--sig-risk)', statusColor: 'var(--sig-risk)' },
  danger: { borderColor: '#b84a4a', statusColor: '#b84a4a', bg: '#faf5f5' },
}

interface DrugCardProps {
  drug: DrugCardData
  onAddToChecklist?: (title: string) => void
  added?: boolean
}

export function DrugCard({ drug, onAddToChecklist, added }: DrugCardProps) {
  const style = IMPACT_STYLES[drug.impact] || IMPACT_STYLES.ok

  return (
    <div style={{
      background: style.bg || 'var(--bg-raised)',
      borderLeft: `4px solid ${style.borderColor}`,
      borderRadius: '0 6px 6px 0',
      padding: '14px 18px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
        <span style={{ fontSize: 12, fontWeight: 600 }}>{drug.drugClass}</span>
        <span style={{ fontSize: 9, fontWeight: 500, color: style.statusColor }}>
          {drug.statusText}
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--text)', lineHeight: 1.6 }}>
        {drug.description}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text-secondary)', marginTop: 6 }}>
        {drug.category === 'substance' ? 'Affects: ' : 'Drugs affected: '}{drug.drugList}
      </div>
      {drug.dangerNote && (
        <div style={{
          marginTop: 10, padding: '10px 14px',
          background: '#faf5f5', border: '1px solid #d4a0a0', borderRadius: 4,
        }}>
          <div style={{ fontSize: 9, fontWeight: 600, color: '#b84a4a', marginBottom: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{drug.category === 'substance' ? 'Interaction warning' : 'Discuss with prescriber'}</span>
            {onAddToChecklist && (
              <button
                className="btn"
                style={{
                  fontSize: '9px',
                  padding: '1px 6px',
                  flexShrink: 0,
                  opacity: added ? 0.4 : 0.6,
                  color: added ? 'var(--sig-benefit)' : 'var(--primary)',
                  borderColor: added ? 'var(--sig-benefit)' : 'var(--border)',
                  cursor: added ? 'default' : 'pointer',
                }}
                disabled={added}
                onClick={(e) => {
                  e.stopPropagation()
                  const noteSnippet = drug.dangerNote!.length > 60 ? drug.dangerNote!.slice(0, 60) + '...' : drug.dangerNote!
                  onAddToChecklist(`${drug.drugClass}: ${noteSnippet}`)
                }}
                onMouseEnter={e => { if (!added) e.currentTarget.style.opacity = '1' }}
                onMouseLeave={e => { e.currentTarget.style.opacity = added ? '0.4' : '0.6' }}
              >
                {added ? 'ADDED' : '+'}
              </button>
            )}
          </div>
          <div style={{ fontSize: 9, color: 'var(--text)', lineHeight: 1.6 }}>
            {drug.dangerNote}
          </div>
        </div>
      )}
    </div>
  )
}
