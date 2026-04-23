import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  fetchWisdomWarriors,
  createWisdomWarrior,
  createWisdomWarriorsBulk,
  updateWisdomWarrior,
  deleteWisdomWarrior,
  fetchWisdomWarriorsMonthlyViews,
  fetchWisdomWarriorsSnapshotRuns,
  type WisdomWarriorMonthlyViewsQuery,
} from "../api/wisdomWarriors"
import type { WisdomWarriorCreate, WisdomWarriorUpdate } from "../types/wisdomWarrior"

const QK = ["wisdom-warriors"] as const

export function useWisdomWarriors() {
  return useQuery({ queryKey: QK, queryFn: fetchWisdomWarriors })
}

export function useWisdomWarriorsMonthlyViews(query?: WisdomWarriorMonthlyViewsQuery) {
  return useQuery({
    queryKey: [...QK, "monthly-views", query],
    queryFn: () => fetchWisdomWarriorsMonthlyViews(query as WisdomWarriorMonthlyViewsQuery),
    enabled: Boolean(query?.month) && typeof query?.snapshotRunId === "number",
  })
}

export function useWisdomWarriorsSnapshotRuns() {
  return useQuery({
    queryKey: [...QK, "snapshot-runs"],
    queryFn: fetchWisdomWarriorsSnapshotRuns,
  })
}

export function useCreateWisdomWarrior() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: WisdomWarriorCreate) => createWisdomWarrior(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
  })
}

export function useBulkCreateWisdomWarriors() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (items: WisdomWarriorCreate[]) => createWisdomWarriorsBulk(items),
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
