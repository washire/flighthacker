/**
 * useSearch — TanStack Query hook that:
 * 1. POSTs to create a search (Phase 1)
 * 2. Polls GET /search/:id every 3 seconds until phase = "complete"
 */
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createSearch, pollSearch } from "../api/search";
import type { SearchRequest, SearchResponse } from "../api/search";
import { useSearchStore } from "../stores/searchStore";

const POLL_INTERVAL_MS = 3000;

export function useSearch() {
  const queryClient = useQueryClient();
  const { setPhase1, setPhase2, phase1 } = useSearchStore();

  const searchMutation = useMutation({
    mutationFn: async (req: SearchRequest) => {
      const result = await createSearch(req);
      setPhase1(result);
      return result;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["search", data.search_id], data);
    },
  });

  const searchId = phase1?.search_id ?? null;
  const isComplete = phase1?.phase === "complete";

  const pollQuery = useQuery({
    queryKey: ["search", searchId],
    queryFn: () => pollSearch(searchId!),
    enabled: !!searchId && !isComplete,
    refetchInterval: (query) => {
      const data = query.state.data as SearchResponse | undefined;
      if (data?.phase === "complete") return false;
      return POLL_INTERVAL_MS;
    },
  });

  // Update store when poll returns new data — useEffect avoids side effects in select
  useEffect(() => {
    const data = pollQuery.data;
    if (!data) return;
    if (data.phase === "complete" || data.phase === "phase_2") {
      setPhase2(data);
    }
  }, [pollQuery.data]);

  return {
    search: searchMutation.mutate,
    isSearching: searchMutation.isPending,
    isPolling: pollQuery.isFetching,
    isComplete:
      pollQuery.data?.phase === "complete" || phase1?.phase === "complete",
    error: searchMutation.error ?? pollQuery.error,
  };
}
