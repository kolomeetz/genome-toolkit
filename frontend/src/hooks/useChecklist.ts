import { useState, useEffect, useCallback } from 'react'

export interface ChecklistItem {
  id: string
  gene_symbol: string
  action_type: string
  title: string
  done: boolean
  done_at: string | null
  notes: string | null
  practical_category: string
  health_domain: string
  created_at: string
}

export type GroupBy = 'evidence' | 'practical' | 'gene' | 'domain' | 'status'
export type FilterStatus = 'all' | 'pending' | 'done'

export function useChecklist() {
  const [items, setItems] = useState<ChecklistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [groupBy, setGroupBy] = useState<GroupBy>('evidence')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')

  // Fetch from API
  const refresh = useCallback(async () => {
    try {
      const res = await fetch('/api/actions')
      if (res.ok) {
        const data = await res.json()
        setItems(data.actions || [])
      }
    } catch {
      console.warn('[genome-toolkit] Checklist API unreachable')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // Toggle done (optimistic)
  const toggleDone = useCallback(async (id: string) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, done: !item.done, done_at: !item.done ? new Date().toISOString() : null } : item
    ))
    try {
      const item = items.find(i => i.id === id)
      await fetch(`/api/actions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ done: item ? !item.done : true }),
      })
    } catch { /* optimistic, ignore */ }
  }, [items])

  // Add item
  const addItem = useCallback(async (title: string, geneSymbol = 'custom', actionType = 'consider', practicalCategory = '', healthDomain = '') => {
    try {
      const res = await fetch('/api/actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          gene_symbol: geneSymbol,
          action_type: actionType,
          practical_category: practicalCategory,
          health_domain: healthDomain,
        }),
      })
      if (res.ok) {
        await refresh()
      }
    } catch { /* ignore */ }
  }, [refresh])

  // Delete item
  const deleteItem = useCallback(async (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id))
    try {
      await fetch(`/api/actions/${id}`, { method: 'DELETE' })
    } catch { /* optimistic */ }
  }, [])

  // Filtered items
  const filtered = items.filter(item => {
    if (filterStatus === 'pending') return !item.done
    if (filterStatus === 'done') return item.done
    return true
  })

  // Grouped items
  const grouped = (() => {
    const groups: Record<string, ChecklistItem[]> = {}
    for (const item of filtered) {
      let key: string
      switch (groupBy) {
        case 'evidence': key = item.action_type || 'other'; break
        case 'practical': key = item.practical_category || 'uncategorized'; break
        case 'gene': key = item.gene_symbol || 'custom'; break
        case 'domain': key = item.health_domain || 'uncategorized'; break
        case 'status': key = item.done ? 'done' : 'pending'; break
      }
      if (!groups[key]) groups[key] = []
      groups[key].push(item)
    }
    return groups
  })()

  const pendingCount = items.filter(i => !i.done).length
  const doneCount = items.filter(i => i.done).length
  const uniqueGenes = [...new Set(items.map(i => i.gene_symbol).filter(g => g !== 'custom'))]

  return {
    items, filtered, grouped, loading,
    groupBy, setGroupBy,
    filterStatus, setFilterStatus,
    toggleDone, addItem, deleteItem, refresh,
    pendingCount, doneCount, uniqueGenes,
  }
}
