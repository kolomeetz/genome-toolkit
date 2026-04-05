import { useState } from 'react'

// ── Types ──────────────────────────────────────────────────────────────────

type RiskStatus = 'actionable' | 'monitor' | 'optimal' | 'nodata'

interface GeneMini {
  symbol: string
  variant: string
  evidenceTier: string
  status: 'actionable' | 'monitor' | 'optimal'
  description: string
}

interface ActionMini {
  type: 'consider' | 'monitor' | 'discuss'
  text: string
}

interface MortalityCause {
  rank: number
  cause: string
  pct: number
  populationBarPct: number
  personalBarPct: number
  status: RiskStatus
  genesText: string
  statusText: string
  narrative?: string
  genes?: GeneMini[]
  actions?: ActionMini[]
}

// ── Color helpers ──────────────────────────────────────────────────────────

const STATUS_COLORS: Record<RiskStatus, string> = {
  actionable: 'var(--sig-risk)',
  monitor: 'var(--sig-monitor)',
  optimal: 'var(--sig-benefit)',
  nodata: 'var(--text-tertiary)',
}

const STATUS_LABELS: Record<RiskStatus, string> = {
  actionable: 'Actionable',
  monitor: 'Monitor',
  optimal: 'Optimal',
  nodata: 'No Data',
}

const ACTION_TYPE_COLORS: Record<'consider' | 'monitor' | 'discuss', string> = {
  consider: 'var(--sig-risk)',
  monitor: 'var(--sig-monitor)',
  discuss: 'var(--primary)',
}

const ACTION_TYPE_LABELS: Record<'consider' | 'monitor' | 'discuss', string> = {
  consider: 'Consider',
  monitor: 'Monitor',
  discuss: 'Discuss',
}

// ── Mock data ──────────────────────────────────────────────────────────────

const CAUSES: MortalityCause[] = [
  {
    rank: 1,
    cause: 'Cardiovascular Disease',
    pct: 31,
    populationBarPct: 62,
    personalBarPct: 35,
    status: 'actionable',
    genesText: 'MTHFR (homocysteine), APOE, LPA',
    statusText: 'Actionable — 3 genes, 3 actions',
    narrative:
      'You carry MTHFR C677T T/T, which can elevate homocysteine — a known cardiovascular risk factor. You also have one APOE e4 allele, associated with higher LDL cholesterol. These are among the most actionable cardiovascular genetics findings because effective interventions exist for both.',
    genes: [
      {
        symbol: 'MTHFR C677T',
        variant: 'T/T',
        evidenceTier: 'E2 STRONG',
        status: 'actionable',
        description:
          'Elevated homocysteine risk. Directly actionable with methylfolate supplementation and monitoring.',
      },
      {
        symbol: 'APOE',
        variant: 'e3/e4',
        evidenceTier: 'E1 GOLD',
        status: 'actionable',
        description:
          'One risk allele. Associated with higher LDL and cardiovascular risk. Responsive to diet and statin therapy.',
      },
      {
        symbol: 'LPA',
        variant: 'rs10455872',
        evidenceTier: 'E2 STRONG',
        status: 'monitor',
        description:
          'Slightly elevated Lp(a). Independent risk factor, not modifiable by lifestyle. Monitor with blood test.',
      },
    ],
    actions: [
      {
        type: 'consider',
        text: 'Methylfolate supplementation (400–800 mcg/day) to support homocysteine metabolism',
      },
      {
        type: 'monitor',
        text: 'Test homocysteine, lipid panel (LDL, Lp(a)), and ApoB annually',
      },
      {
        type: 'discuss',
        text: 'Ask your doctor about APOE e4 status and whether early statin therapy is appropriate for you',
      },
    ],
  },
  {
    rank: 2,
    cause: 'Cancer',
    pct: 24,
    populationBarPct: 48,
    personalBarPct: 10,
    status: 'optimal',
    genesText: 'No high-risk variants detected (BRCA1/2, CHEK2, APC normal)',
    statusText: 'Optimal — standard screening applies',
  },
  {
    rank: 3,
    cause: 'Accidents & Substance-Related',
    pct: 12,
    populationBarPct: 24,
    personalBarPct: 28,
    status: 'actionable',
    genesText: 'DRD2 (reward), GABRA2 (sedative sensitivity), CYP2D6 (metabolism)',
    statusText: 'Actionable — see Addiction Profile',
    narrative:
      'DRD2 Taq1A and GABRA2 variants point to elevated reward-seeking and sedative sensitivity respectively. CYP2D6 poor metabolizer status affects how many substances are processed, increasing toxicity risk at standard doses.',
    genes: [
      {
        symbol: 'DRD2',
        variant: 'Taq1A A1/A2',
        evidenceTier: 'E2 STRONG',
        status: 'actionable',
        description: 'Reduced dopamine receptor density — associated with reward deficit and higher addiction susceptibility.',
      },
      {
        symbol: 'GABRA2',
        variant: 'rs279858',
        evidenceTier: 'E2 STRONG',
        status: 'actionable',
        description: 'Increased sedative sensitivity, linked to elevated risk for alcohol use disorder.',
      },
      {
        symbol: 'CYP2D6',
        variant: 'Poor metabolizer',
        evidenceTier: 'E1 GOLD',
        status: 'monitor',
        description: 'Reduced metabolism of opioids, many antidepressants. Standard doses may have stronger-than-expected effects.',
      },
    ],
    actions: [
      {
        type: 'consider',
        text: 'Review CYP2D6 status with prescribing physicians — dosing adjustments may be warranted',
      },
      {
        type: 'monitor',
        text: 'Be aware of heightened reward sensitivity when evaluating recreational substance use',
      },
      {
        type: 'discuss',
        text: 'Discuss full pharmacogenomic implications with a clinical pharmacist',
      },
    ],
  },
  {
    rank: 4,
    cause: 'Cerebrovascular Disease (Stroke)',
    pct: 6,
    populationBarPct: 12,
    personalBarPct: 18,
    status: 'monitor',
    genesText: 'MTHFR (homocysteine), APOE',
    statusText: 'Monitor — homocysteine levels',
  },
  {
    rank: 5,
    cause: 'Suicide',
    pct: 5,
    populationBarPct: 10,
    personalBarPct: 5,
    status: 'optimal',
    genesText: 'SLC6A4 (optimal), COMT (monitor), BDNF (optimal)',
    statusText: 'Protective serotonin/neuroplasticity factors',
  },
  {
    rank: 6,
    cause: 'Diabetes (Type 2)',
    pct: 4,
    populationBarPct: 8,
    personalBarPct: 12,
    status: 'monitor',
    genesText: 'TCF7L2 (risk allele), FTO (obesity-associated)',
    statusText: 'Monitor — consider HbA1c testing',
  },
  {
    rank: 7,
    cause: 'Liver Disease',
    pct: 3,
    populationBarPct: 6,
    personalBarPct: 4,
    status: 'optimal',
    genesText: 'ALDH2 (normal), PNPLA3 (normal), HFE (normal)',
    statusText: 'Optimal — no elevated risk variants',
  },
  {
    rank: 8,
    cause: "Alzheimer's / Dementia",
    pct: 3,
    populationBarPct: 6,
    personalBarPct: 15,
    status: 'actionable',
    genesText: 'APOE e3/e4 (one risk allele)',
    statusText: 'Actionable — lifestyle interventions strongly modify risk',
    narrative:
      'One APOE e4 allele approximately doubles lifetime risk relative to e3/e3. Critically, risk is substantially modifiable: aerobic exercise, sleep quality, cardiovascular health, and cognitive engagement all have strong evidence for risk reduction in e4 carriers.',
    genes: [
      {
        symbol: 'APOE',
        variant: 'e3/e4',
        evidenceTier: 'E1 GOLD',
        status: 'actionable',
        description: 'Heterozygous e4 carrier. ~2× relative risk increase. Highly responsive to lifestyle interventions; risk is not destiny.',
      },
    ],
    actions: [
      {
        type: 'consider',
        text: 'Regular aerobic exercise (150 min/week) — strongest single modifiable risk factor for APOE e4 carriers',
      },
      {
        type: 'monitor',
        text: 'Track sleep quality and treat any obstructive sleep apnea — sleep clears amyloid via glymphatic system',
      },
      {
        type: 'discuss',
        text: "Ask your doctor about APOE e4 status and whether periodic cognitive screening is appropriate",
      },
    ],
  },
  {
    rank: 9,
    cause: 'Chronic Respiratory Disease',
    pct: 2,
    populationBarPct: 4,
    personalBarPct: 4,
    status: 'nodata',
    genesText: 'SERPINA1 not genotyped',
    statusText: 'No genetic data available',
  },
  {
    rank: 10,
    cause: 'Kidney Disease',
    pct: 2,
    populationBarPct: 4,
    personalBarPct: 3,
    status: 'optimal',
    genesText: 'APOL1 (normal for EUR ancestry)',
    statusText: 'Optimal',
  },
]

// ── Summary stats ──────────────────────────────────────────────────────────

function getSummaryStats(causes: MortalityCause[]) {
  return {
    actionable: causes.filter((c) => c.status === 'actionable').length,
    monitor: causes.filter((c) => c.status === 'monitor').length,
    optimal: causes.filter((c) => c.status === 'optimal').length,
    nodata: causes.filter((c) => c.status === 'nodata').length,
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────

function GeneMiniCard({ gene }: { gene: GeneMini }) {
  const borderColor = STATUS_COLORS[gene.status]
  return (
    <div
      style={{
        background: 'var(--bg)',
        borderLeft: `3px solid ${borderColor}`,
        borderRadius: '0 6px 6px 0',
        padding: '10px 14px',
        flex: '1 1 180px',
        minWidth: 160,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: 4,
        }}
      >
        <span
          style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
            letterSpacing: '0.04em',
          }}
        >
          {gene.symbol}
        </span>
        <span
          style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 500,
            padding: '2px 6px',
            borderRadius: 3,
            letterSpacing: '0.08em',
            color: 'var(--bg-raised)',
            background: borderColor,
            whiteSpace: 'nowrap',
            marginLeft: 6,
          }}
        >
          {gene.evidenceTier}
        </span>
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-xs)',
          color: 'var(--text-secondary)',
          marginBottom: 3,
        }}
      >
        {gene.variant}
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-xs)',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
        }}
      >
        {gene.description}
      </div>
    </div>
  )
}

function ActionMiniCard({ action }: { action: ActionMini }) {
  const borderColor = ACTION_TYPE_COLORS[action.type]
  return (
    <div
      style={{
        background: 'var(--bg)',
        borderLeft: `3px solid ${borderColor}`,
        borderRadius: '0 6px 6px 0',
        padding: '10px 14px',
      }}
    >
      <div
        style={{
          fontSize: 'var(--font-size-xs)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          color: borderColor,
          marginBottom: 3,
        }}
      >
        {ACTION_TYPE_LABELS[action.type]}
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-sm)',
          lineHeight: 1.6,
        }}
      >
        {action.text}
      </div>
    </div>
  )
}

function ExpandedDetail({ cause }: { cause: MortalityCause }) {
  return (
    <div
      style={{
        background: 'var(--bg-raised)',
        border: '1.5px solid var(--border)',
        borderTop: 'none',
        borderRadius: '0 0 6px 6px',
        padding: '18px 20px',
        marginLeft: 36,
        marginBottom: 4,
      }}
    >
      {cause.narrative && (
        <div
          style={{
            fontSize: 'var(--font-size-sm)',
            lineHeight: 1.7,
            marginBottom: 16,
            borderLeft: '3px solid var(--primary)',
            paddingLeft: 14,
            color: 'var(--text)',
          }}
        >
          {cause.narrative}
        </div>
      )}

      {cause.genes && cause.genes.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: 10,
            flexWrap: 'wrap',
            marginBottom: 12,
          }}
        >
          {cause.genes.map((gene) => (
            <GeneMiniCard key={gene.symbol} gene={gene} />
          ))}
        </div>
      )}

      {cause.actions && cause.actions.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {cause.actions.map((action, idx) => (
            <ActionMiniCard key={idx} action={action} />
          ))}
        </div>
      )}
    </div>
  )
}

function PersonalBar({ status, widthPct }: { status: RiskStatus; widthPct: number }) {
  const isNoData = status === 'nodata'
  return (
    <div
      style={{
        height: 14,
        width: `${widthPct}%`,
        borderRadius: 3,
        background: isNoData ? 'var(--border)' : STATUS_COLORS[status],
        opacity: isNoData ? 0.3 : 0.75,
        border: isNoData ? '1px dashed var(--border-strong)' : undefined,
      }}
    />
  )
}

function MortalityRow({
  cause,
  isExpanded,
  onToggle,
}: {
  cause: MortalityCause
  isExpanded: boolean
  onToggle: () => void
}) {
  const hasDetail = !!(cause.narrative || (cause.genes && cause.genes.length > 0))
  const statusColor = STATUS_COLORS[cause.status]

  return (
    <>
      <div
        onClick={hasDetail ? onToggle : undefined}
        style={{
          display: 'flex',
          alignItems: 'stretch',
          gap: 0,
          cursor: hasDetail ? 'pointer' : 'default',
          background: isExpanded ? 'var(--bg-raised)' : 'transparent',
          borderRadius: isExpanded ? '6px 6px 0 0' : 6,
          border: isExpanded ? '1.5px solid var(--border)' : '1.5px solid transparent',
          borderBottom: isExpanded ? 'none' : undefined,
          marginLeft: 0,
          padding: '8px 0',
          transition: 'background 0.12s',
        }}
        onMouseEnter={(e) => {
          if (hasDetail && !isExpanded) {
            e.currentTarget.style.background = 'var(--bg-inset)'
          }
        }}
        onMouseLeave={(e) => {
          if (!isExpanded) {
            e.currentTarget.style.background = 'transparent'
          }
        }}
      >
        {/* Rank */}
        <div
          style={{
            width: 36,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 600,
            color: 'var(--text-tertiary)',
            flexShrink: 0,
          }}
        >
          {cause.rank}
        </div>

        {/* Bar area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4, paddingRight: 12 }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 600,
                letterSpacing: '0.04em',
              }}
            >
              {cause.cause}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
              {cause.pct}% of deaths
            </span>
          </div>

          {/* Population bar */}
          <div
            style={{
              height: 8,
              width: `${cause.populationBarPct}%`,
              background: 'var(--border)',
              borderRadius: 2,
            }}
          />

          {/* Personal bar */}
          <PersonalBar status={cause.status} widthPct={cause.personalBarPct} />

          {/* Detail row */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--text-secondary)',
            }}
          >
            <span>{cause.genesText}</span>
            <span
              style={{
                fontWeight: 500,
                color: statusColor,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              {cause.statusText}
              {hasDetail && (
                <span style={{ fontSize: 10 }}>{isExpanded ? '▾' : '▸'}</span>
              )}
            </span>
          </div>
        </div>
      </div>

      {isExpanded && hasDetail && <ExpandedDetail cause={cause} />}
    </>
  )
}

// ── Legend ─────────────────────────────────────────────────────────────────

function BarLegend() {
  const items: Array<{ label: string; height: number; color: string; opacity: number; dashed?: boolean }> = [
    { label: 'Population prevalence', height: 8, color: 'var(--border)', opacity: 1 },
    { label: 'Actionable genetic factors', height: 14, color: 'var(--sig-risk)', opacity: 0.75 },
    { label: 'Monitor', height: 14, color: 'var(--sig-monitor)', opacity: 0.75 },
    { label: 'Optimal / protective', height: 14, color: 'var(--sig-benefit)', opacity: 0.75 },
    { label: 'No genetic data', height: 14, color: 'var(--border)', opacity: 0.3, dashed: true },
  ]

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px 20px',
        marginBottom: 24,
        fontSize: 'var(--font-size-xs)',
        color: 'var(--text-secondary)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}
    >
      {items.map((item) => (
        <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div
            style={{
              width: 24,
              height: item.height,
              background: item.color,
              opacity: item.opacity,
              borderRadius: 2,
              border: item.dashed ? '1px dashed var(--border-strong)' : undefined,
              flexShrink: 0,
            }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

interface RiskLandscapeProps {
  onExport?: (format: 'pdf' | 'md' | 'doctor') => void
}

export function RiskLandscape({ onExport }: RiskLandscapeProps) {
  const [expandedRank, setExpandedRank] = useState<number | null>(1)
  const stats = getSummaryStats(CAUSES)

  function handleToggle(rank: number) {
    setExpandedRank((prev) => (prev === rank ? null : rank))
  }

  function handleExport(format: 'pdf' | 'md' | 'doctor') {
    onExport?.(format)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      {/* Hero */}
      <div
        style={{
          padding: '48px 24px 36px',
          borderBottom: '1px solid var(--border)',
          maxWidth: 1100,
          margin: '0 auto',
          width: '100%',
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: '0.08em',
            marginBottom: 10,
          }}
        >
          Mortality & Risk Landscape
        </div>
        <div
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
            maxWidth: 720,
          }}
        >
          The top causes of mortality for your demographic, overlaid with your personal genetic factors.
          Knowledge is power — knowing where to focus attention lets you take informed action.
        </div>

        {/* Stats */}
        <div style={{ display: 'flex', gap: 24, marginTop: 20, flexWrap: 'wrap' }}>
          {[
            { value: stats.actionable, label: 'Actionable areas', color: 'var(--sig-risk)' },
            { value: stats.monitor, label: 'Monitor', color: 'var(--sig-monitor)' },
            { value: stats.optimal, label: 'Optimal / no risk', color: 'var(--sig-benefit)' },
            { value: stats.nodata, label: 'No data', color: 'var(--text-tertiary)' },
          ].map(({ value, label, color }) => (
            <div key={label}>
              <div style={{ fontSize: 20, fontWeight: 600, color }}>{value}</div>
              <div
                style={{
                  fontSize: 'var(--font-size-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.12em',
                  color: 'var(--text-secondary)',
                  marginTop: 2,
                }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ padding: '28px 24px', maxWidth: 1100, margin: '0 auto', width: '100%', flex: 1 }}>
        {/* Context block */}
        <div
          style={{
            background: 'var(--bg-raised)',
            border: '1.5px solid var(--primary)',
            borderRadius: 6,
            padding: '14px 16px',
            marginBottom: 28,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
          }}
        >
          <span
            style={{
              fontSize: 'var(--font-size-md)',
              color: 'var(--primary)',
              flexShrink: 0,
              fontWeight: 600,
            }}
          >
            i
          </span>
          <div style={{ fontSize: 'var(--font-size-xs)', lineHeight: 1.6 }}>
            Population bars show how common each cause of death is for{' '}
            <strong>males, 30–44, European ancestry</strong> (based on your profile). Your personal
            bar shows where you have relevant genetic variants. Having variants does not predict
            outcomes — it shows where awareness and prevention can make a difference.
          </div>
        </div>

        {/* Bar legend */}
        <BarLegend />

        {/* Mortality rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32 }}>
          {CAUSES.map((cause) => (
            <MortalityRow
              key={cause.rank}
              cause={cause}
              isExpanded={expandedRank === cause.rank}
              onToggle={() => handleToggle(cause.rank)}
            />
          ))}
        </div>

        {/* Export buttons */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 6,
            paddingTop: 12,
            borderTop: '1px dashed var(--border-dashed)',
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
              onClick={() => handleExport(format)}
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
      <div
        style={{
          padding: '8px 24px',
          borderTop: '1px dashed var(--border-dashed)',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--text-tertiary)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        <span>
          {CAUSES.length} causes &middot; male 30–44 EUR &middot; {stats.actionable} actionable
        </span>
        <span>GENOME_TOOLKIT // RISK LANDSCAPE</span>
      </div>
    </div>
  )
}

export type { RiskStatus, MortalityCause }
export { STATUS_COLORS as RISK_STATUS_COLORS, STATUS_LABELS as RISK_STATUS_LABELS }
