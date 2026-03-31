/**
 * Results tab — ranked list of all hacking method results.
 * Shows Phase 1 immediately, updates as Phase 2 arrives.
 */
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { router } from "expo-router";
import { useSearchStore } from "../../stores/searchStore";
import { useSearch } from "../../hooks/useSearch";
import { formatGbpRound } from "../../api/search";
import type { ItineraryResult } from "../../api/search";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

const METHOD_LABELS: Record<string, string> = {
  direct_cheapest: "Direct",
  hub_arbitrage: "Hub Arbitrage",
  nearby_origin: "Alt. Origin",
  nearby_destination: "Alt. Destination",
  open_jaw: "Open Jaw",
  fare_zone_open_jaw: "Fare Zone",
  mixed_cabin: "Mixed Cabin",
  positioning_flight: "Positioning",
  apd_avoidance: "APD Avoidance",
  avios_reward: "Avios",
  oneworld_portal: "OW Portal",
  crazy_mode: "CRAZY",
};

function ResultCard({
  item,
  onPress,
}: {
  item: ItineraryResult;
  onPress: () => void;
}) {
  const saving = item.saving.vs_direct_saving_gbp ?? 0;
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.cardHeader}>
        <Text style={styles.methodBadge}>
          {METHOD_LABELS[item.method] ?? item.method}
        </Text>
        {item.is_self_transfer && (
          <Text style={styles.selfTransfer}>Self-transfer</Text>
        )}
        {item.is_award && (
          <Text style={styles.awardBadge}>AVIOS</Text>
        )}
      </View>

      <View style={styles.cardBody}>
        <Text style={styles.price}>{formatGbpRound(item.cost.total_gbp)}</Text>
        <View style={styles.cardRight}>
          {saving > 0 && (
            <Text style={styles.saving}>Save {formatGbpRound(saving)}</Text>
          )}
          <Text style={styles.duration}>
            {Math.floor(item.total_duration_minutes / 60)}h{" "}
            {item.total_duration_minutes % 60}m
          </Text>
        </View>
      </View>

      <Text style={styles.headline} numberOfLines={2}>
        {item.saving.headline}
      </Text>
    </TouchableOpacity>
  );
}

export default function ResultsScreen() {
  const { getSortedResults, sortBy, setSortBy, phase1, phase2 } =
    useSearchStore();
  const { isPolling } = useSearch();
  const results = getSortedResults();
  const isPhase2Done = phase2?.phase === "complete";

  if (!phase1 && !phase2) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>
          Run a search to see results here.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Status bar */}
      <View style={styles.statusBar}>
        <Text style={styles.statusText}>
          {isPhase2Done
            ? `${results.length} results`
            : isPolling
            ? "Digging deeper..."
            : `${results.length} results so far`}
        </Text>
        {isPolling && <ActivityIndicator color={Colors.teal[400]} size="small" />}
      </View>

      {/* Sort controls */}
      <View style={styles.sortRow}>
        {(["price", "duration", "saving"] as const).map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.sortBtn, sortBy === s && styles.sortBtnActive]}
            onPress={() => setSortBy(s)}
          >
            <Text
              style={[styles.sortText, sortBy === s && styles.sortTextActive]}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={results}
        keyExtractor={(r) => r.result_id}
        renderItem={({ item }) => (
          <ResultCard
            item={item}
            onPress={() => {
              useSearchStore.getState().selectResult(item);
              router.push(`/result/${item.result_id}`);
            }}
          />
        )}
        contentContainerStyle={styles.list}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.navy[950] },
  empty: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyText: { color: Colors.gray[500], fontSize: FontSize.md },
  statusBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.navy[900],
  },
  statusText: { color: Colors.gray[300], fontSize: FontSize.sm },
  sortRow: {
    flexDirection: "row",
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  sortBtn: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.navy[800],
    borderWidth: 1,
    borderColor: Colors.navy[600],
  },
  sortBtnActive: { borderColor: Colors.orange[500] },
  sortText: { color: Colors.gray[300], fontSize: FontSize.sm },
  sortTextActive: { color: Colors.orange[400] },
  list: { padding: Spacing.md },
  card: {
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.navy[600],
  },
  cardHeader: { flexDirection: "row", gap: Spacing.xs, marginBottom: Spacing.xs },
  methodBadge: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.teal[400],
    backgroundColor: `${Colors.teal[500]}20`,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    overflow: "hidden",
  },
  selfTransfer: {
    fontSize: FontSize.xs,
    color: Colors.warning,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
  },
  awardBadge: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.orange[400],
    backgroundColor: `${Colors.orange[500]}20`,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    overflow: "hidden",
  },
  cardBody: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginBottom: Spacing.xs,
  },
  price: {
    fontSize: FontSize.xxl,
    fontWeight: "800",
    color: Colors.white,
  },
  cardRight: { alignItems: "flex-end" },
  saving: { fontSize: FontSize.sm, color: Colors.teal[400], fontWeight: "700" },
  duration: { fontSize: FontSize.xs, color: Colors.gray[500] },
  headline: { fontSize: FontSize.sm, color: Colors.gray[300], lineHeight: 18 },
});
