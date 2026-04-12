import { useState, useEffect } from 'react'

export interface SystemConfig {
  name: string
  tags: string[]
  domains: string[]
  gene_count: number
  genes: string[]
}

export interface GoalPill {
  id: string
  label: string
  actionType: 'navigate' | 'filter'
  target: string
  tooltip: string
}

interface SystemsResponse {
  systems: Record<string, SystemConfig>
  unconfigured: Record<string, { gene_count: number; genes: string[] }>
  goal_pills: GoalPill[]
}

interface UseSystemsReturn {
  systems: Record<string, SystemConfig>
  goalPills: GoalPill[]
  loading: boolean
  getSystemsForDomain: (domain: string) => Record<string, SystemConfig>
}

let cached: SystemsResponse | null = null
let cachePromise: Promise<SystemsResponse> | null = null

export function useSystems(): UseSystemsReturn {
  const [data, setData] = useState<SystemsResponse | null>(cached)
  const [loading, setLoading] = useState(cached === null)

  useEffect(() => {
    if (cached !== null) {
      setData(cached)
      setLoading(false)
      return
    }

    let cancelled = false

    if (!cachePromise) {
      cachePromise = fetch('/api/vault/systems')
        .then((res) => {
          if (!res.ok) throw new Error(`Systems API: ${res.status}`)
          return res.json()
        })
        .then((result: SystemsResponse) => {
          cached = result
          return result
        })
        .catch((err) => {
          cachePromise = null
          throw err
        })
    }

    cachePromise
      .then((result) => {
        if (cancelled) return
        setData(result)
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        console.error('[useSystems]', err)
        setLoading(false)
      })

    return () => { cancelled = true }
  }, [])

  const getSystemsForDomain = (domain: string): Record<string, SystemConfig> => {
    if (!data) return {}
    const result: Record<string, SystemConfig> = {}
    for (const [key, sys] of Object.entries(data.systems)) {
      if (sys.domains.includes(domain)) {
        result[key] = sys
      }
    }
    return result
  }

  return {
    systems: data?.systems ?? {},
    goalPills: data?.goal_pills ?? [],
    loading,
    getSystemsForDomain,
  }
}
