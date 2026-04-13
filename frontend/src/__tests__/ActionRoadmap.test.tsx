import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ActionRoadmap } from '../components/mental-health/ActionRoadmap'
import type { ActionData, GeneData, PathwaySection } from '../types/genomics'

const mockGenes: GeneData[] = [
  {
    symbol: 'MTHFR', variant: 'C677T', rsid: 'rs1801133', genotype: 'T/T',
    status: 'actionable', evidenceTier: 'E1', studyCount: 50,
    description: 'Reduced folate conversion.', actionCount: 2,
    categories: ['mood'], pathway: 'Methylation Pathway',
  },
  {
    symbol: 'SLC6A4', variant: '5-HTTLPR', rsid: 'rs25531', genotype: 'S/L',
    status: 'monitor', evidenceTier: 'E2', studyCount: 30,
    description: 'Serotonin transporter.', actionCount: 1,
    categories: ['mood'], pathway: 'Serotonin & Neuroplasticity',
  },
  {
    symbol: 'BDNF', variant: 'Val66Met', rsid: 'rs6265', genotype: 'G/G',
    status: 'optimal', evidenceTier: 'E2', studyCount: 20,
    description: 'Normal BDNF function.', actionCount: 1,
    categories: ['mood'], pathway: 'Serotonin & Neuroplasticity',
  },
]

const mockSections: PathwaySection[] = [
  {
    narrative: { pathway: 'Methylation Pathway', status: 'actionable', body: '', priority: '', hint: '', geneCount: 1, actionCount: 2 },
    genes: [mockGenes[0]],
  },
  {
    narrative: { pathway: 'Serotonin & Neuroplasticity', status: 'monitor', body: '', priority: '', hint: '', geneCount: 2, actionCount: 2 },
    genes: [mockGenes[1], mockGenes[2]],
  },
]

const mockActions: Record<string, ActionData[]> = {
  MTHFR: [
    { id: 'mthfr-0', type: 'consider', title: 'Methylfolate 400-800mcg/day', description: '', evidenceTier: 'E1', studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
    { id: 'mthfr-1', type: 'monitor', title: 'Test homocysteine levels', description: '', evidenceTier: 'E1', studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
  ],
  SLC6A4: [
    { id: 'slc6a4-0', type: 'discuss', title: 'Discuss SSRI dose with psychiatrist', description: '', evidenceTier: 'E2', studyCount: 30, tags: [], geneSymbol: 'SLC6A4', done: false },
  ],
  BDNF: [
    { id: 'bdnf-0', type: 'try', title: 'Morning sunlight 15-20min', description: '', evidenceTier: 'E2', studyCount: 20, tags: [], geneSymbol: 'BDNF', done: false },
  ],
}

describe('ActionRoadmap', () => {
  it('renders roadmap header', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.getByText('ACTION ROADMAP')).toBeInTheDocument()
  })

  it('renders top 5 actions by default (or all if fewer)', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.getByText('Methylfolate 400-800mcg/day')).toBeInTheDocument()
    expect(screen.getByText('Test homocysteine levels')).toBeInTheDocument()
    expect(screen.getByText('Discuss SSRI dose with psychiatrist')).toBeInTheDocument()
    expect(screen.getByText('Morning sunlight 15-20min')).toBeInTheDocument()
  })

  it('ranks actionable E1 genes first', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    const items = screen.getAllByTestId('roadmap-item')
    expect(items[0]).toHaveTextContent('MTHFR')
  })

  it('shows gene symbol and metadata for each action', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    const metadataElements = screen.getAllByText(/MTHFR.*Actionable.*E1/)
    expect(metadataElements.length).toBeGreaterThan(0)
  })

  it('calls onAddToChecklist when + button clicked', () => {
    const onAdd = vi.fn()
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={onAdd} />)
    const addButtons = screen.getAllByLabelText('Add to checklist')
    fireEvent.click(addButtons[0])
    expect(onAdd).toHaveBeenCalledTimes(1)
  })

  it('respects category filter', () => {
    render(
      <ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} activeCategory="sleep" />,
    )
    expect(screen.queryByTestId('roadmap-item')).not.toBeInTheDocument()
  })

  it('respects action type filter', () => {
    render(
      <ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} activeActionType="discuss" />,
    )
    expect(screen.getByText('Discuss SSRI dose with psychiatrist')).toBeInTheDocument()
    expect(screen.queryByText('Methylfolate 400-800mcg/day')).not.toBeInTheDocument()
  })

  it('hides expand toggle when 5 or fewer actions', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.queryByText(/SHOW ALL/)).not.toBeInTheDocument()
  })

  it('shows expand toggle and expands when more than 5 actions', () => {
    // Create 6+ actions by adding extra to MTHFR
    const manyActions = {
      ...mockActions,
      MTHFR: [
        ...mockActions.MTHFR,
        { id: 'mthfr-2', type: 'try' as const, title: 'Exercise regularly', description: '', evidenceTier: 'E1' as const, studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
        { id: 'mthfr-3', type: 'consider' as const, title: 'Reduce alcohol intake', description: '', evidenceTier: 'E1' as const, studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
        { id: 'mthfr-4', type: 'monitor' as const, title: 'Track energy levels', description: '', evidenceTier: 'E1' as const, studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
      ],
    }
    render(<ActionRoadmap sections={mockSections} actions={manyActions} onAddToChecklist={vi.fn()} />)
    // Should show SHOW ALL with count
    expect(screen.getByText(/SHOW ALL 7/)).toBeInTheDocument()
    // Only 5 visible by default
    expect(screen.getAllByTestId('roadmap-item')).toHaveLength(5)
    // Click expand
    fireEvent.click(screen.getByText(/SHOW ALL 7/))
    // Now all 7 visible
    expect(screen.getAllByTestId('roadmap-item')).toHaveLength(7)
    // Toggle shows SHOW LESS
    expect(screen.getByText('SHOW LESS')).toBeInTheDocument()
  })

  it('hides roadmap when no actions available', () => {
    render(<ActionRoadmap sections={mockSections} actions={{}} onAddToChecklist={vi.fn()} />)
    expect(screen.queryByText('ACTION ROADMAP')).not.toBeInTheDocument()
  })
})
