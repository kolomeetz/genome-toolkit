import { useState } from 'react'
import { NarrativeBlock } from '../mental-health/NarrativeBlock'
import { GeneCard } from '../mental-health/GeneCard'
import type { GeneData } from '../../types/genomics'
import { useAddictionData } from '../../hooks/useAddictionData'
import type { SubstanceCard } from '../../hooks/useAddictionData'
import { GenomeGlyph } from '../GenomeGlyph'
import { printPage, downloadFile, addictionToMarkdown } from '../../lib/export'

// ─── Sub-components ──────────────────────────────────────────────────────────

function SubstanceCardItem({ substance, added, onAdd }: { substance: SubstanceCard; added?: boolean; onAdd?: () => void }) {
  return (
    <div className="substance-card" style={{
      background: 'var(--bg-raised)',
      borderLeft: `4px solid ${substance.borderColor}`,
      border: `1.5px solid ${substance.borderColor}`,
      borderRadius: 6,
      padding: '14px 16px',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: 8,
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
          {substance.name}
        </span>
        <span style={{ fontSize: 9, fontWeight: 500, color: substance.statusColor, fontFamily: 'var(--font-mono)' }}>
          {substance.status}
        </span>
      </div>
      <div style={{ fontSize: 10, lineHeight: 1.6, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
        {substance.description}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text-secondary)', marginTop: 8, fontFamily: 'var(--font-mono)' }}>
        {substance.genes}
      </div>
      <div style={{
        marginTop: 10,
        padding: '10px 14px',
        background: 'var(--bg-inset)',
        borderRadius: 4,
      }}>
        <div style={{
          fontSize: 9,
          fontWeight: 600,
          color: 'var(--text)',
          marginBottom: 4,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontFamily: 'var(--font-mono)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>{substance.harmTitle}</span>
          {onAdd && (
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
              onClick={(e) => { e.stopPropagation(); onAdd(); }}
              onMouseEnter={e => { if (!added) e.currentTarget.style.opacity = '1' }}
              onMouseLeave={e => { e.currentTarget.style.opacity = added ? '0.4' : '0.6' }}
            >
              {added ? 'ADDED' : '+'}
            </button>
          )}
        </div>
        <div style={{ fontSize: 10, lineHeight: 1.6, fontFamily: 'var(--font-mono)' }}>
          {substance.harmText}
        </div>
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

interface AddictionProfileProps {
  onExport?: (format: string) => void
  onAddToChecklist?: (title: string, gene: string) => void
}

export function AddictionProfile({ onExport: _onExport, onAddToChecklist }: AddictionProfileProps) {
  const { pathways: PATHWAYS, substances: SUBSTANCES, loading, totalGenes: TOTAL_GENES, actionableCount: ACTIONABLE_COUNT } = useAddictionData()
  const [addedSubstances, setAddedSubstances] = useState<Set<string>>(new Set())
  const handleGeneClick = (_gene: GeneData) => {
    // no-op for now — could open a drawer in a future iteration
  }

  if (loading) return <div className="label">LOADING_DATA...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>

      {/* Hero header */}
      <div className="hero-header" style={{
        padding: '40px 24px 32px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        gap: 24,
        alignItems: 'flex-start',
      }}>
        <GenomeGlyph
          genotypes={PATHWAYS.flatMap(s => s.genes.map(g => g.genotype))}
          size={100}
          label="reward profile"
        />
        <div style={{ flex: 1 }}>
        <div style={{
          fontSize: 28,
          fontWeight: 600,
          letterSpacing: '0.08em',
          fontFamily: 'var(--font-mono)',
          marginBottom: 10,
        }}>
          Addiction &amp; Reward Profile
        </div>
        <div style={{
          fontSize: 13,
          color: 'var(--text-secondary)',
          lineHeight: 1.7,
          maxWidth: 760,
          fontFamily: 'var(--font-mono)',
        }}>
          How your genetics relate to reward sensitivity, substance metabolism, and dependence patterns.
          This is context for self-understanding and harm reduction, not diagnosis.
        </div>
        <div className="stats-row" style={{ display: 'flex', gap: 24, marginTop: 20 }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 20, fontWeight: 600, color: 'var(--sig-risk)', fontFamily: 'var(--font-mono)' }}>
              {TOTAL_GENES}
            </span>
            <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--text-secondary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
              Genes analyzed
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 20, fontWeight: 600, color: 'var(--sig-reduced)', fontFamily: 'var(--font-mono)' }}>
              {ACTIONABLE_COUNT}
            </span>
            <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--text-secondary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
              Actionable findings
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 20, fontWeight: 600, color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
              {SUBSTANCES.length}
            </span>
            <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--text-secondary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
              Substances profiled
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 20, fontWeight: 600, color: 'var(--sig-benefit)', fontFamily: 'var(--font-mono)' }}>
              {PATHWAYS.length}
            </span>
            <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.12em', color: 'var(--text-secondary)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
              Pathways mapped
            </span>
          </div>
        </div>
        </div>{/* end flex wrapper */}
      </div>

      {/* Main content */}
      <div className="section-content" style={{ padding: '24px 24px 0' }}>

        {/* Context block */}
        <div style={{
          background: 'var(--bg-raised)',
          border: '1.5px solid var(--primary)',
          borderRadius: 6,
          padding: '16px 18px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
        }}>
          <span style={{
            fontSize: 'var(--font-size-md)',
            color: 'var(--primary)',
            flexShrink: 0,
            fontWeight: 600,
            fontFamily: 'var(--font-mono)',
          }}>
            i
          </span>
          <div style={{ fontSize: 11, lineHeight: 1.7, fontFamily: 'var(--font-mono)' }}>
            This profile shows how your genetics relate to reward sensitivity, substance metabolism, and dependence patterns.
            Having variants associated with higher sensitivity does <strong>not</strong> mean you will develop
            dependence — genetics is one factor among many, including environment, mental health, social context, and personal
            history. This information is provided for <strong>self-understanding and harm reduction</strong>, not diagnosis.
          </div>
        </div>

        {/* Pathway sections */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24, marginBottom: 24 }}>
          {PATHWAYS.map(section => (
            <div key={section.narrative.pathway} className="pathway-row" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <NarrativeBlock narrative={section.narrative} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {section.genes.map(gene => (
                  <GeneCard key={`${gene.symbol}-${gene.rsid}`} gene={gene} onClick={handleGeneClick} />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Divider */}
        <hr style={{ border: 'none', borderTop: '1px dashed var(--border-dashed)', margin: '4px 0 24px' }} />

        {/* Substance harm reduction section */}
        <div style={{
          fontSize: 10,
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          marginBottom: 12,
          color: 'var(--text)',
          fontFamily: 'var(--font-mono)',
        }}>
          Your substance-specific harm reduction notes
        </div>
        <p style={{ fontSize: 10, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.6, fontFamily: 'var(--font-mono)' }}>
          Based on your genetic profile across all pathways. These are summaries — see PGx panel for full metabolism details.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {SUBSTANCES.map(substance => {
            const firstGene = substance.genes.match(/(\w+)/)?.[1] || 'custom'
            return (
              <SubstanceCardItem
                key={substance.name}
                substance={substance}
                added={addedSubstances.has(substance.name)}
                onAdd={onAddToChecklist ? () => {
                  setAddedSubstances(prev => new Set(prev).add(substance.name))
                  onAddToChecklist(`${substance.name}: ${substance.harmTitle}`, firstGene)
                } : undefined}
              />
            )
          })}
        </div>

        {/* Export buttons */}
        <div
          className="export-buttons"
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 6,
            paddingTop: 12,
            borderTop: '1px dashed var(--border-dashed)',
            marginBottom: 24,
          }}
        >
          {(
            [
              { format: 'pdf', label: 'Export PDF', accent: false },
              { format: 'md', label: 'Export MD', accent: false },
              { format: 'doctor', label: 'Print for doctor', accent: true },
            ] as const
          ).map(({ format, label, accent }) => (
            <button
              key={format}
              onClick={() => {
                if (format === 'md') {
                  const md = addictionToMarkdown(PATHWAYS, SUBSTANCES)
                  downloadFile(md, `addiction-profile-${new Date().toISOString().slice(0, 10)}.md`)
                } else if (format === 'doctor') {
                  printPage('doctor')
                } else {
                  printPage('pdf')
                }
              }}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--font-size-xs)',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                padding: '4px 10px',
                border: `1px solid ${accent ? 'var(--accent)' : 'var(--border-strong)'}`,
                background: 'transparent',
                color: accent ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                borderRadius: 2,
              }}
            >
              {label}
            </button>
          ))}
        </div>

      </div>

      {/* Footer */}
      <footer style={{
        padding: 'var(--space-xs) var(--space-lg)',
        borderTop: '1px dashed var(--border-dashed)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span className="label">
          {TOTAL_GENES} GENES &middot; {SUBSTANCES.length} SUBSTANCES &middot; HARM REDUCTION MODE
        </span>
        <span className="label">GENOME_TOOLKIT // ADDICTION &amp; REWARD PROFILE</span>
      </footer>

    </div>
  )
}
