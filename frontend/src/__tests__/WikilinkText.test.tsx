import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WikilinkText } from '../components/mental-health/WikilinkText'

const defaults = {
  dashboardGenes: new Set(['COMT', 'MTHFR']),
  onNavigateToGene: vi.fn(),
  onReadInChat: vi.fn(),
}

function renderText(text: string, overrides = {}) {
  return render(<WikilinkText text={text} {...defaults} {...overrides} />)
}

describe('WikilinkText', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders plain text without wikilinks unchanged', () => {
    renderText('No links here')
    expect(screen.getByText('No links here')).toBeTruthy()
  })

  it('renders wikilink as clickable gene name', () => {
    renderText('See [[COMT]] for details')
    expect(screen.getByText('COMT')).toBeTruthy()
    expect(screen.getByText(/See/)).toBeTruthy()
  })

  it('clicking a dashboard gene calls onNavigateToGene', () => {
    const onNavigateToGene = vi.fn()
    renderText('See [[COMT]]', { onNavigateToGene })
    fireEvent.click(screen.getByText('COMT'))
    expect(onNavigateToGene).toHaveBeenCalledWith('COMT')
  })

  it('clicking a non-dashboard gene calls onReadInChat', () => {
    const onReadInChat = vi.fn()
    renderText('See [[GAD1]]', { onReadInChat })
    fireEvent.click(screen.getByText('GAD1'))
    expect(onReadInChat).toHaveBeenCalledWith('GAD1')
  })

  it('note icon always calls onReadInChat even for dashboard genes', () => {
    const onReadInChat = vi.fn()
    renderText('See [[COMT]]', { onReadInChat })
    const noteIcon = screen.getByTitle('Read full COMT note in chat')
    fireEvent.click(noteIcon)
    expect(onReadInChat).toHaveBeenCalledWith('COMT')
  })

  it('handles multiple wikilinks in one string', () => {
    renderText('[[COMT]] and [[MTHFR]] interact')
    expect(screen.getByText('COMT')).toBeTruthy()
    expect(screen.getByText('MTHFR')).toBeTruthy()
  })

  it('handles wikilinks with aliases [[Target|Alias]]', () => {
    renderText('See [[COMT|catechol-O-methyltransferase]]')
    expect(screen.getByText('catechol-O-methyltransferase')).toBeTruthy()
  })

  it('keyboard Enter triggers navigation for dashboard gene', () => {
    const onNavigateToGene = vi.fn()
    renderText('[[MTHFR]]', { onNavigateToGene })
    fireEvent.keyDown(screen.getByText('MTHFR'), { key: 'Enter' })
    expect(onNavigateToGene).toHaveBeenCalledWith('MTHFR')
  })
})
