import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FilterBar } from '../components/mental-health/FilterBar'

describe('FilterBar', () => {
  it('renders category filter chips', () => {
    render(
      <FilterBar activeCategory={null} activeActionType={null}
        onCategoryChange={vi.fn()} onActionTypeChange={vi.fn()}
        onClearAll={vi.fn()} onExport={vi.fn()} />
    )
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('Mood')).toBeInTheDocument()
    expect(screen.getByText('Stress')).toBeInTheDocument()
    expect(screen.getByText('Sleep')).toBeInTheDocument()
    expect(screen.getByText('Focus')).toBeInTheDocument()
  })

  it('renders action type filter chips', () => {
    render(
      <FilterBar activeCategory={null} activeActionType={null}
        onCategoryChange={vi.fn()} onActionTypeChange={vi.fn()}
        onClearAll={vi.fn()} onExport={vi.fn()} />
    )
    expect(screen.getByText('Consider')).toBeInTheDocument()
    expect(screen.getByText('Monitor')).toBeInTheDocument()
    expect(screen.getByText('Discuss')).toBeInTheDocument()
    expect(screen.getByText('Try')).toBeInTheDocument()
  })

  it('calls onCategoryChange when chip clicked', () => {
    const onChange = vi.fn()
    render(
      <FilterBar activeCategory={null} activeActionType={null}
        onCategoryChange={onChange} onActionTypeChange={vi.fn()}
        onClearAll={vi.fn()} onExport={vi.fn()} />
    )
    fireEvent.click(screen.getByText('Mood'))
    expect(onChange).toHaveBeenCalledWith('mood')
  })

  it('renders export buttons', () => {
    render(
      <FilterBar activeCategory={null} activeActionType={null}
        onCategoryChange={vi.fn()} onActionTypeChange={vi.fn()}
        onClearAll={vi.fn()} onExport={vi.fn()} />
    )
    expect(screen.getByText('Export PDF')).toBeInTheDocument()
    expect(screen.getByText('Export MD')).toBeInTheDocument()
    expect(screen.getByText('Print for doctor')).toBeInTheDocument()
  })
})
