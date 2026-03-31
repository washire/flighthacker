/**
 * Result detail screen — full breakdown of one itinerary.
 * Opens as a modal from the results list.
 */
import { View, Text, ScrollView, StyleSheet, Linking, TouchableOpacity } from "react-native";
import { useSearchStore } from "../../stores/searchStore";
import { formatGbp, formatGbpRound } from "../../api/search";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

function LegRow({ leg }: { leg: any }) {
  const dep = new Date(leg.departure_at);
  const arr = new Date(leg.arrival_at);
  const fmt = (d: Date) =>
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <View style={styles.legRow}>
      <View style={styles.legTimes}>
        <Text style={styles.legTime}>{fmt(dep)}</Text>
        <Text style={styles.legArrow}>→</Text>
        <Text style={styles.legTime}>{fmt(arr)}</Text>
      </View>
      <Text style={styles.legRoute}>
        {leg.origin} → {leg.destination}
      </Text>
      <Text style={styles.legInfo}>
        {leg.airline_name} · {leg.flight_number} · {leg.cabin_class}
      </Text>
      <Text style={styles.legInfo}>
        {Math.floor(leg.duration_minutes / 60)}h {leg.duration_minutes % 60}m ·{" "}
        {leg.stops === 0 ? "Direct" : `${leg.stops} stop`}
      </Text>
      <Text style={[styles.legInfo, { color: leg.carry_on_included ? Colors.success : Colors.error }]}>
        Carry-on: {leg.carry_on_included ? "Included" : "Charged"}
      </Text>
      {leg.checked_bag_included ? (
        <Text style={[styles.legInfo, { color: Colors.success }]}>
          1 checked bag included
        </Text>
      ) : leg.checked_bag_fee_gbp > 0 ? (
        <Text style={[styles.legInfo, { color: Colors.warning }]}>
          Checked bag: {formatGbp(leg.checked_bag_fee_gbp)}
        </Text>
      ) : null}
    </View>
  );
}

export default function ResultDetailScreen() {
  const { selectedResult } = useSearchStore();

  if (!selectedResult) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>No result selected.</Text>
      </View>
    );
  }

  const r = selectedResult;
  const c = r.cost;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Price hero */}
      <View style={styles.hero}>
        <Text style={styles.heroPrice}>{formatGbpRound(c.total_gbp)}</Text>
        {r.saving.vs_direct_saving_gbp && r.saving.vs_direct_saving_gbp > 0 && (
          <Text style={styles.heroSaving}>
            Saves {formatGbpRound(r.saving.vs_direct_saving_gbp)} vs direct
          </Text>
        )}
        <Text style={styles.heroHeadline}>{r.saving.headline}</Text>
      </View>

      {/* Explanation */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>HOW THIS WORKS</Text>
        <Text style={styles.detail}>{r.saving.detail}</Text>
      </View>

      {/* Outbound legs */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>OUTBOUND FLIGHTS</Text>
        {r.outbound_legs.map((leg, i) => (
          <LegRow key={i} leg={leg} />
        ))}
      </View>

      {/* Return legs */}
      {r.return_legs.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>RETURN FLIGHTS</Text>
          {r.return_legs.map((leg, i) => (
            <LegRow key={i} leg={leg} />
          ))}
        </View>
      )}

      {/* Cost breakdown */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>COST BREAKDOWN</Text>
        <CostLine label="Base fare" pence={c.base_fare_gbp} />
        <CostLine label="Taxes" pence={c.taxes_gbp} />
        {c.carrier_surcharges_gbp > 0 && (
          <CostLine label="Carrier surcharges (YQ)" pence={c.carrier_surcharges_gbp} />
        )}
        {c.bags_gbp > 0 && <CostLine label="Bags" pence={c.bags_gbp} />}
        {c.ground_transport_gbp > 0 && (
          <CostLine label="Ground transport" pence={c.ground_transport_gbp} />
        )}
        {c.positioning_flight_gbp > 0 && (
          <CostLine label="Positioning flight" pence={c.positioning_flight_gbp} />
        )}
        <View style={styles.divider} />
        <CostLine label="TOTAL" pence={c.total_gbp} bold />
        {c.avios_required && (
          <Text style={styles.aviosNote}>
            Or: {c.avios_required.toLocaleString()} Avios
            {c.cash_copay_gbp ? ` + ${formatGbp(c.cash_copay_gbp)} cash` : ""}
            {c.pence_per_point ? ` (${c.pence_per_point}p/pt)` : ""}
          </Text>
        )}
      </View>

      {/* Warnings */}
      {r.is_self_transfer && (
        <View style={styles.warning}>
          <Text style={styles.warningText}>
            Self-transfer required — these are two separate bookings.
            Allow at least 3 hours between flights. You are responsible for
            making your connecting flight.
          </Text>
        </View>
      )}

      {/* Book button */}
      {r.deep_link && (
        <TouchableOpacity
          style={styles.bookButton}
          onPress={() => Linking.openURL(r.deep_link!)}
        >
          <Text style={styles.bookButtonText}>BOOK ON GOOGLE FLIGHTS</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}

function CostLine({ label, pence, bold }: { label: string; pence: number; bold?: boolean }) {
  return (
    <View style={styles.costLine}>
      <Text style={[styles.costLabel, bold && styles.costBold]}>{label}</Text>
      <Text style={[styles.costValue, bold && styles.costBold]}>
        {formatGbp(pence)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.navy[950] },
  content: { padding: Spacing.lg },
  empty: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyText: { color: Colors.gray[500] },
  hero: {
    alignItems: "center",
    paddingVertical: Spacing.xl,
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.lg,
  },
  heroPrice: { fontSize: FontSize.hero, fontWeight: "900", color: Colors.white },
  heroSaving: { fontSize: FontSize.md, color: Colors.teal[400], fontWeight: "700", marginTop: 4 },
  heroHeadline: {
    fontSize: FontSize.sm,
    color: Colors.gray[300],
    marginTop: Spacing.sm,
    textAlign: "center",
    paddingHorizontal: Spacing.lg,
  },
  section: { marginBottom: Spacing.lg },
  sectionTitle: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.gray[500],
    letterSpacing: 1.5,
    marginBottom: Spacing.sm,
  },
  detail: { fontSize: FontSize.sm, color: Colors.gray[300], lineHeight: 20 },
  legRow: {
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
  },
  legTimes: { flexDirection: "row", alignItems: "center", gap: Spacing.sm, marginBottom: 4 },
  legTime: { fontSize: FontSize.lg, fontWeight: "700", color: Colors.white },
  legArrow: { fontSize: FontSize.lg, color: Colors.orange[400] },
  legRoute: { fontSize: FontSize.md, fontWeight: "600", color: Colors.white, marginBottom: 2 },
  legInfo: { fontSize: FontSize.xs, color: Colors.gray[500], marginTop: 2 },
  costLine: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: Spacing.xs,
  },
  costLabel: { fontSize: FontSize.sm, color: Colors.gray[300] },
  costValue: { fontSize: FontSize.sm, color: Colors.gray[300] },
  costBold: { fontWeight: "700", color: Colors.white, fontSize: FontSize.md },
  divider: { height: 1, backgroundColor: Colors.navy[600], marginVertical: Spacing.xs },
  aviosNote: { fontSize: FontSize.sm, color: Colors.orange[400], marginTop: Spacing.sm },
  warning: {
    backgroundColor: `${Colors.warning}20`,
    borderRadius: BorderRadius.md,
    borderLeftWidth: 3,
    borderLeftColor: Colors.warning,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
  },
  warningText: { fontSize: FontSize.sm, color: Colors.warning, lineHeight: 20 },
  bookButton: {
    backgroundColor: Colors.orange[500],
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: "center",
    marginBottom: Spacing.xl,
  },
  bookButtonText: {
    color: Colors.white,
    fontSize: FontSize.md,
    fontWeight: "800",
    letterSpacing: 1.5,
  },
});
