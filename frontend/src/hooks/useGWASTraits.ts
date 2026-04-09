import { useEffect, useState } from 'react'

export interface GWASTrait {
  trait: string
  display_name: string | null
  source: string
  publication: string
  n_hits: number
  threshold: number
}

export function useGWASTraits() {
  const [traits, setTraits] = useState<GWASTrait[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/gwas/traits')
      .then(res => res.json())
      .then(data => setTraits(data.traits ?? []))
      .catch(() => setTraits([]))
      .finally(() => setLoading(false))
  }, [])

  return { traits, loading }
}
