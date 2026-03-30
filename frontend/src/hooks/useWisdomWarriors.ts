import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  fetchWisdomWarriors,
  createWisdomWarrior,
  updateWisdomWarrior,
  deleteWisdomWarrior,
  fetchWisdomWarriorsMonthlyViews,
} from "../api/wisdomWarriors"
import type { WisdomWarriorCreate, WisdomWarriorUpdate } from "../types/wisdomWarrior"

const QK = ["wisdom-warriors"] as const

export function useWisdomWarriors() {
  return useQuery({ queryKey: QK, queryFn: fetchWisdomWarriors })
}

export function useWisdomWarriorsMonthlyViews(month: string) {
  return useQuery({
    queryKey: [...QK, "monthly-views", month],
    queryFn: () => fetchWisdomWarriorsMonthlyViews(month),
    enabled: !!month,
  })
}

export function useCreateWisdomWarrior() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: WisdomWarriorCreate) => createWisdomWarrior(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })
}

export function useUpdateWisdomWarrior() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: WisdomWarriorUpdate }) => updateWisdomWarrior(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })
}

export function useDeleteWisdomWarrior() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteWisdomWarrior(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })
}
