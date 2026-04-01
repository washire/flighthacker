/**
 * Search tab — the main screen.
 */
import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { useSearch } from "../../hooks/useSearch";
import { useSearchStore } from "../../stores/searchStore";
import { AirportPicker, type AirportSelection } from "../../components/AirportPicker";
import { DatePickerModal } from "../../components/DatePickerModal";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

function todayPlusDays(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().split("T")[0];
}

export default function SearchScreen() {
  const [origin, setOrigin] = useState<AirportSelection | null>({
    iata: "LHR",
    airports: ["LHR", "LGW", "STN", "LTN", "LCY"],
    city: "London",
    label: "London — all airports",
  });
  const [destination, setDestination] = useState<AirportSelection | null>(null);
  const [outboundDate, setOutboundDate] = useState(todayPlusDays(30));
  const [returnDate, setReturnDate] = useState("");
  const [isReturn, setIsReturn] = useState(false);
  const [crazyMode, setCrazyMode] = useState(false);

  const { search, isSearching } = useSearch();
  const { reset } = useSearchStore();

  function handleSearch() {
    if (!origin || !destination) {
      Alert.alert("Missing airports", "Please select both origin and destination.");
      return;
    }
    if (!outboundDate) {
      Alert.alert("Missing date", "Please select a departure date.");
      return;
    }
    reset();
    search(
      {
        origin: origin.iata,
        destination: destination.iata,
        outbound_date: outboundDate,
        return_date: isReturn && returnDate ? returnDate : null,
        crazy_mode: crazyMode,
        // City-mode fields
        origin_airports: origin.airports.length > 1 ? origin.airports : null,
        destination_airports: destination.airports.length > 1 ? destination.airports : null,
        origin_city: origin.city,
        destination_city: destination.city,
      },
      {
        onSuccess: () => {
          router.push("/(tabs)/results");
        },
        onError: (err: any) => {
          Alert.alert(
            "Search failed",
            err?.message ?? "Could not connect to server. Please try again."
          );
        },
      }
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.tagline}>Smart Travel, Hacked Prices.</Text>

      <View style={styles.card}>
        <AirportPicker label="FROM" value={origin} onChange={setOrigin} />
        <AirportPicker label="TO" value={destination} onChange={setDestination} />

        {/* One-way / Return toggle */}
        <View style={styles.tripTypeRow}>
          <TouchableOpacity
            style={[styles.tripBtn, !isReturn && styles.tripBtnActive]}
            onPress={() => setIsReturn(false)}
          >
            <Text style={[styles.tripBtnText, !isReturn && styles.tripBtnTextActive]}>
              One way
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tripBtn, isReturn && styles.tripBtnActive]}
            onPress={() => setIsReturn(true)}
          >
            <Text style={[styles.tripBtnText, isReturn && styles.tripBtnTextActive]}>
              Return
            </Text>
          </TouchableOpacity>
        </View>

        <DatePickerModal
          label="DEPARTURE"
          value={outboundDate}
          onChange={setOutboundDate}
        />

        {isReturn && (
          <DatePickerModal
            label="RETURN"
            value={returnDate}
            onChange={setReturnDate}
            minDate={outboundDate}
          />
        )}

        <TouchableOpacity
          style={[styles.crazyToggle, crazyMode && styles.crazyActive]}
          onPress={() => setCrazyMode(!crazyMode)}
        >
          <Text style={[styles.crazyText, crazyMode && styles.crazyTextActive]}>
            {crazyMode ? "⚡ CRAZY MODE ON — all routes, all methods" : "Enable Crazy Mode"}
          </Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.button, isSearching && styles.buttonDisabled]}
        onPress={handleSearch}
        disabled={isSearching}
      >
        {isSearching ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator color={Colors.white} />
            <Text style={[styles.buttonText, { marginLeft: Spacing.sm }]}>Searching…</Text>
          </View>
        ) : (
          <Text style={styles.buttonText}>HACK IT</Text>
        )}
      </TouchableOpacity>

      <Text style={styles.hint}>
        Searches all airport combinations simultaneously.{"\n"}
        Phase 1 results in ~3 seconds.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.navy[950] },
  content: { padding: Spacing.lg, paddingTop: Spacing.xl },
  tagline: {
    fontSize: FontSize.xl,
    fontWeight: "700",
    color: Colors.orange[400],
    marginBottom: Spacing.xl,
    textAlign: "center",
  },
  card: {
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
  },
  tripTypeRow: {
    flexDirection: "row",
    marginTop: Spacing.md,
    marginBottom: Spacing.xs,
    gap: Spacing.sm,
  },
  tripBtn: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.navy[600],
    alignItems: "center",
  },
  tripBtnActive: {
    borderColor: Colors.orange[500],
    backgroundColor: `${Colors.orange[500]}20`,
  },
  tripBtnText: {
    color: Colors.gray[400],
    fontSize: FontSize.sm,
    fontWeight: "600",
  },
  tripBtnTextActive: { color: Colors.orange[400] },
  crazyToggle: {
    marginTop: Spacing.md,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.gray[500],
    padding: Spacing.sm,
    alignItems: "center",
  },
  crazyActive: {
    borderColor: Colors.orange[500],
    backgroundColor: `${Colors.orange[500]}20`,
  },
  crazyText: { color: Colors.gray[300], fontSize: FontSize.sm, fontWeight: "600" },
  crazyTextActive: { color: Colors.orange[400] },
  button: {
    backgroundColor: Colors.orange[500],
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: "center",
    marginBottom: Spacing.md,
  },
  buttonDisabled: { opacity: 0.6 },
  loadingRow: { flexDirection: "row", alignItems: "center" },
  buttonText: {
    color: Colors.white,
    fontSize: FontSize.lg,
    fontWeight: "800",
    letterSpacing: 2,
  },
  hint: {
    color: Colors.gray[500],
    fontSize: FontSize.xs,
    textAlign: "center",
    lineHeight: 18,
  },
});
