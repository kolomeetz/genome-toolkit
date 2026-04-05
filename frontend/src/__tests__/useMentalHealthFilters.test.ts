import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useMentalHealthFilters } from '../hooks/useMentalHealthFilters'

describe('useMentalHealthFilters', () => {
  it('starts with all filters showing everything', () => {
    const { result } = renderHook(() => useMentalHealthFilters())
    expect(result.current.activeCategory).toBe(null)
    expect(result.current.activeActionType).toBe(null)
  })

  it('toggles category filter', () => {
    const { result } = renderHook(() => useMentalHealthFilters())
    act(() => result.current.setCategory('mood'))
    expect(result.current.activeCategory).toBe('mood')
    act(() => result.current.setCategory('mood'))
    expect(result.current.activeCategory).toBe(null)
  })

  it('toggles action type filter', () => {
    const { result } = renderHook(() => useMentalHealthFilters())
    act(() => result.current.setActionType('consider'))
    expect(result.current.activeActionType).toBe('consider')
  })

  it('clears all filters', () => {
    const { result } = renderHook(() => useMentalHealthFilters())
    act(() => {
      result.current.setCategory('mood')
      result.current.setActionType('consider')
    })
    act(() => result.current.clearAll())
    expect(result.current.activeCategory).toBe(null)
    expect(result.current.activeActionType).toBe(null)
  })

  it('filters genes by category', () => {
    const { result } = renderHook(() => useMentalHealthFilters())
    const genes = [
      { categories: ['mood', 'stress'] },
      { categories: ['sleep'] },
      { categories: ['mood'] },
    ]
    act(() => result.current.setCategory('mood'))
    const filtered = genes.filter(g => result.current.matchesGene(g as any))
    expect(filtered).toHaveLength(2)
  })
})
