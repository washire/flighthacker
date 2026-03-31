/**
 * Global search state — Zustand store.
 * Holds the current search request, Phase 1 results, and Phase 2 results.
 */
import { create } from "zustand";
import type { SearchRequest, SearchResponse, ItineraryResult } from "../api/search";

interface SearchState {
  // Current search inputs
  request: SearchRequest | null;
  setRequest: (req: SearchRequest) => void;

  // Results
  phase1: SearchResponse | null;
  phase2: SearchResponse | null;
  setPhase1: (resp: SearchResponse) => void;
  setPhase2: (resp: SearchResponse) => void;

  // Selected result (for detail view)
  selectedResult: ItineraryResult | null;
  selectResult: (result: ItineraryResult | null) => void;

  // Sort/filter
  sortBy: "price" | "duration" | "saving";
  setSortBy: (sort: "price" | "duration" | "saving") => void;
  showAwardsOnly: boolean;
  setShowAwardsOnly: (v: boolean) => void;

  // Derived: sorted results from whichever phase is furthest along
  getSortedResults: () => ItineraryResult[];

  // Reset
  reset: () => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
  request: null,
  setRequest: (req) => set({ request: req }),

  phase1: null,
  phase2: null,
  setPhase1: (resp) => set({ phase1: resp }),
  setPhase2: (resp) => set({ phase2: resp }),

  selectedResult: null,
  selectResult: (result) => set({ selectedResult: result }),

  sortBy: "price",
  setSortBy: (sort) => set({ sortBy: sort }),
  showAwardsOnly: false,
  setShowAwardsOnly: (v) => set({ showAwardsOnly: v }),

  getSortedResults: () => {
    const { phase2, phase1, sortBy, showAwardsOnly } = get();
    const source = phase2 ?? phase1;
    if (!source) return [];

    let results = [...source.results];

    if (showAwardsOnly) {
      results = results.filter((r) => r.is_award);
    }

    if (sortBy === "price") {
      results.sort((a, b) => a.cost.total_gbp - b.cost.total_gbp);
    } else if (sortBy === "duration") {
      results.sort((a, b) => a.total_duration_minutes - b.total_duration_minutes);
    } else if (sortBy === "saving") {
      results.sort(
        (a, b) =>
          (b.saving.vs_direct_saving_gbp ?? 0) -
          (a.saving.vs_direct_saving_gbp ?? 0)
      );
    }

    return results;
  },

  reset: () =>
    set({
      request: null,
      phase1: null,
      phase2: null,
      selectedResult: null,
      sortBy: "price",
      showAwardsOnly: false,
    }),
}));
