/**
 * Search API calls — wraps POST /api/v1/search and GET /api/v1/search/:id
 */
import { api } from "./client";

export interface SearchRequest {
  origin: string;
  destination: string;
  outbound_date: string;       // ISO date "2025-08-01"
  return_date?: string | null;
  passengers?: number;
  cabin_class?: "economy" | "premium_economy" | "business" | "first";
  avios_balance?: number | null;
  pence_per_point?: number | null;
  crazy_mode?: boolean;
}

export interface FlightLeg {
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
  airline_code: string;
  airline_name: string;
  flight_number: string;
  cabin_class: string;
  duration_minutes: number;
  stops: number;
  self_transfer: boolean;
  carry_on_included: boolean;
  checked_bag_included: boolean;
  checked_bag_fee_gbp: number;
  avios_earn: number | null;
}

export interface CostBreakdown {
  base_fare_gbp: number;        // pence
  taxes_gbp: number;
  carrier_surcharges_gbp: number;
  bags_gbp: number;
  ground_transport_gbp: number;
  positioning_flight_gbp: number;
  total_gbp: number;            // pence
  avios_required: number | null;
  cash_copay_gbp: number | null;
  pence_per_point: number | null;
}

export interface ItineraryResult {
  result_id: string;
  method: string;
  outbound_legs: FlightLeg[];
  return_legs: FlightLeg[];
  cost: CostBreakdown;
  saving: {
    headline: string;
    detail: string;
    vs_direct_saving_gbp: number | null;
  };
  total_duration_minutes: number;
  is_self_transfer: boolean;
  is_award: boolean;
  award_program: string | null;
  deep_link: string | null;
}

export interface SearchResponse {
  search_id: string;
  results: ItineraryResult[];
  phase: "phase_1" | "phase_2" | "complete";
  total_results: number;
  cheapest_gbp: number | null;
  generated_at: string;
  cached: boolean;
  direct_price_gbp: number | null;
}

export async function createSearch(
  req: SearchRequest
): Promise<SearchResponse> {
  const resp = await api.post<{ data: SearchResponse }>(
    "/api/v1/search",
    req
  );
  return resp.data;
}

export async function pollSearch(searchId: string): Promise<SearchResponse> {
  const resp = await api.get<{ data: SearchResponse }>(
    `/api/v1/search/${searchId}`
  );
  return resp.data;
}

/** Format pence as "£X.XX" */
export function formatGbp(pence: number): string {
  return `£${(pence / 100).toFixed(2)}`;
}

/** Format pence as "£X" (whole pounds, for display in cards) */
export function formatGbpRound(pence: number): string {
  return `£${Math.round(pence / 100)}`;
}
