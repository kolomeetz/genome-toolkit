import { useState, useCallback } from 'react'
import type { Category, ActionType, GeneData, ActionData } from '../types/genomics'

export function useMentalHealthFilters() {
  const [activeCategory, setActiveCategory] = useState<Category | null>(null)
  const [activeActionType, setActiveActionType] = useState<ActionType | null>(null)

  const setCategory = useCallback((cat: Category) => {
    setActiveCategory(prev => prev === cat ? null : cat)
  }, [])

  const setActionType = useCallback((type: ActionType) => {
    setActiveActionType(prev => prev === type ? null : type)
  }, [])

  const clearAll = useCallback(() => {
    setActiveCategory(null)
    setActiveActionType(null)
  }, [])

  const matchesGene = useCallback((gene: GeneData): boolean => {
    if (activeCategory && !gene.categories.includes(activeCategory)) return false
    return true
  }, [activeCategory])

  const matchesAction = useCallback((action: ActionData): boolean => {
    if (activeActionType && action.type !== activeActionType) return false
    return true
  }, [activeActionType])

  return { activeCategory, activeActionType, setCategory, setActionType, clearAll, matchesGene, matchesAction }
}
