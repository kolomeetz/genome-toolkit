import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

const mockCauses = [
  {
    rank: 1, cause: 'Heart Disease', pct: 23.0,
    populationBarPct: 100, personalBarPct: 80,
    status: 'actionable', genesText: 'APOE, MTHFR',
    statusText: 'Actionable — 1 gene, 1 action',
    narrative: '2 genes analyzed for heart disease risk.',
    genes: [{ symbol: 'APOE', variant: 'E3/E4', evidenceTier: 'E1', status: 'actionable', description: 'Elevated LDL.' }],
    actions: [{ type: 'consider', text: 'Check LDL levels' }],
    confidence: { filled: 2, total: 3, tooltip: '2 genes analyzed, avg evidence E2' },
    timeline: [
      {
        frequency: 'quarterly', label: 'QUARTERLY', color: 'var(--sig-risk)',
        items: [{ name: 'Blood pressure check', type: 'monitor', frequency: 'quarterly', source: 'screening' }],
      },
      {
        frequency: 'once', label: 'ONCE / AS NEEDED', color: 'var(--primary)',
        items: [{ name: 'Check LDL levels', type: 'consider', frequency: 'once', source: 'vault' }],
      },
    ],
  },
  {
    rank: 2, cause: 'Cancer', pct: 21.0,
    populationBarPct: 91, personalBarPct: 27,
    status: 'optimal', genesText: 'SOD2',
    statusText: 'Optimal — no elevated risk variants',
    genes: [{ symbol: 'SOD2', variant: 'C/C', evidenceTier: 'E3', status: 'optimal', description: 'Normal.' }],
    confidence: { filled: 1, total: 3, tooltip: '1 gene analyzed, avg evidence E3' },
  },
  {
    rank: 3, cause: 'Accidents', pct: 8.0,
    populationBarPct: 35, personalBarPct: 11,
    status: 'nodata', genesText: 'No relevant variants detected',
    statusText: 'No genetic data available',
    confidence: { filled: 0, total: 3, tooltip: 'No genes analyzed' },
  },
]

beforeEach(async () => {
  vi.restoreAllMocks()
  vi.resetModules()
  vi.doMock('../hooks/useRiskData', () => ({
    useRiskData: () => ({
      causes: mockCauses,
      demographic: { sex: 'male', age_range: '30-44', ancestry: 'european' },
      loading: false,
    }),
  }))
})

async function renderComponent(props = {}) {
  const mod = await import('../components/risk/RiskLandscape')
  return render(<mod.RiskLandscape {...props} />)
}

describe('RiskLandscape', () => {
  it('renders title', async () => {
    await renderComponent()
    expect(screen.getByText(/Mortality.*Risk Landscape/)).toBeInTheDocument()
  })

  it('renders summary stats', async () => {
    await renderComponent()
    expect(screen.getByText('Actionable areas')).toBeInTheDocument()
    expect(screen.getAllByText('Monitor').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Optimal / no risk')).toBeInTheDocument()
  })

  it('renders all mortality causes', async () => {
    await renderComponent()
    expect(screen.getByText('Heart Disease')).toBeInTheDocument()
    expect(screen.getByText('Cancer')).toBeInTheDocument()
    expect(screen.getByText('Accidents')).toBeInTheDocument()
  })

  it('shows percentage of deaths', async () => {
    await renderComponent()
    expect(screen.getByText('23% of deaths')).toBeInTheDocument()
    expect(screen.getByText('21% of deaths')).toBeInTheDocument()
  })

  it('shows genes text', async () => {
    await renderComponent()
    expect(screen.getByText('APOE, MTHFR')).toBeInTheDocument()
    expect(screen.getByText('No relevant variants detected')).toBeInTheDocument()
  })

  it('shows expanded detail for rank 1 by default', async () => {
    await renderComponent()
    expect(screen.getByText('2 genes analyzed for heart disease risk.')).toBeInTheDocument()
    expect(screen.getByText('APOE')).toBeInTheDocument()
  })

  it('renders timeline groups in expanded detail', async () => {
    await renderComponent()
    expect(screen.getByText('QUARTERLY')).toBeInTheDocument()
    expect(screen.getByText('Blood pressure check')).toBeInTheDocument()
    expect(screen.getByText('ONCE / AS NEEDED')).toBeInTheDocument()
    expect(screen.getByText('Check LDL levels')).toBeInTheDocument()
  })

  it('renders confidence dots for each cause', async () => {
    await renderComponent()
    const heartDots = screen.getByLabelText('2 genes analyzed, avg evidence E2')
    expect(heartDots).toBeInTheDocument()
    const nodataDots = screen.getByLabelText('No genes analyzed')
    expect(nodataDots).toBeInTheDocument()
  })

  it('renders honest risk disclaimer', async () => {
    await renderComponent()
    expect(screen.getByText(/qualitative assessment/)).toBeInTheDocument()
    expect(screen.getByText(/not a calibrated risk score or PRS/)).toBeInTheDocument()
  })

  it('renders demographic in callout', async () => {
    await renderComponent()
    expect(screen.getByText(/males, 30.44, European ancestry/i)).toBeInTheDocument()
  })

  it('renders export bar', async () => {
    await renderComponent()
    expect(screen.getByText('Export PDF')).toBeInTheDocument()
    expect(screen.getByText('Export MD')).toBeInTheDocument()
  })

  it('renders footer with cause count', async () => {
    await renderComponent()
    expect(screen.getByText(/3 causes/)).toBeInTheDocument()
  })

  it('renders bar legend', async () => {
    await renderComponent()
    expect(screen.getByText('Population prevalence')).toBeInTheDocument()
    expect(screen.getByText('Actionable genetic factors')).toBeInTheDocument()
  })
})
