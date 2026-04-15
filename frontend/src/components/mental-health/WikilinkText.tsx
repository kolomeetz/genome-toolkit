import { Fragment } from 'react'

const WIKILINK_RE = /\[\[([^\]|#]+?)(?:#[^\]|]*?)?(?:\|([^\]]*?))?\]\]/g

interface WikilinkTextProps {
  text: string
  /** Genes available on the current dashboard (symbols) */
  dashboardGenes: Set<string>
  /** Navigate to a gene card on the dashboard (scroll + expand) */
  onNavigateToGene: (symbol: string) => void
  /** Open the full vault note in chat */
  onReadInChat: (noteName: string) => void
}

/**
 * Renders plain text with [[wikilinks]] converted to interactive gene links.
 *
 * Click on gene name → expand on dashboard (if present) or read in chat (fallback).
 * Small "note" icon → always opens full vault note in chat.
 */
export function WikilinkText({
  text,
  dashboardGenes,
  onNavigateToGene,
  onReadInChat,
}: WikilinkTextProps) {
  const parts: (string | JSX.Element)[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  // Reset regex state
  WIKILINK_RE.lastIndex = 0
  while ((match = WIKILINK_RE.exec(text)) !== null) {
    const [full, target, alias] = match
    const display = alias || target
    const before = text.slice(lastIndex, match.index)
    if (before) parts.push(before)

    const isOnDashboard = dashboardGenes.has(target)

    parts.push(
      <Fragment key={match.index}>
        <span
          role="link"
          tabIndex={0}
          onClick={() => {
            if (isOnDashboard) {
              onNavigateToGene(target)
            } else {
              onReadInChat(target)
            }
          }}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              if (isOnDashboard) onNavigateToGene(target)
              else onReadInChat(target)
            }
          }}
          style={{
            color: 'var(--primary)',
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            borderBottom: '1px dashed var(--primary-dim)',
          }}
          title={isOnDashboard ? `Go to ${display} on this page` : `Read ${display} vault note`}
        >
          {display}
        </span>
        <span
          role="button"
          tabIndex={0}
          onClick={() => onReadInChat(target)}
          onKeyDown={e => { if (e.key === 'Enter') onReadInChat(target) }}
          style={{
            cursor: 'pointer',
            marginLeft: 3,
            fontSize: '0.85em',
            opacity: 0.5,
            verticalAlign: 'super',
          }}
          title={`Read full ${display} note in chat`}
        >
          {'[n]'}
        </span>
      </Fragment>
    )
    lastIndex = match.index + full.length
  }

  const tail = text.slice(lastIndex)
  if (tail) parts.push(tail)

  return <>{parts}</>
}
