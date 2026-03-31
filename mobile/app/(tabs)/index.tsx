/**
 * Search tab — the main screen.
 * User enters origin/destination/date and hits "Hack It".
 */
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { router } from "expo-router";
import { useSearch } from "../../hooks/useSearch";
import { useSearchStore } from "../../stores/searchStore";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

export default function SearchScreen() {
  const [origin, setOrigin] = useState("LHR");
  const [destination, setDestination] = useState("");
  const [date, setDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().split("T")[0];
  });
  const [crazyMode, setCrazyMode] = useState(false);

  const { search, isSearching } = useSearch();
  const { reset } = useSearchStore();

  function handleSearch() {
    if (!origin || !destination || !date) return;
    reset();
    search(
      { origin, destination, outbound_date: date, crazy_mode: crazyMode },
      {
        onSuccess: () => {
          router.push("/(tabs)/results");
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
        <Text style={styles.label}>FROM</Text>
        <TextInput
          style={styles.input}
          value={origin}
          onChangeText={(t) => setOrigin(t.toUpperCase())}
          placeholder="LHR"
          placeholderTextColor={Colors.gray[500]}
          maxLength={3}
          autoCapitalize="characters"
        />

        <Text style={styles.label}>TO</Text>
        <TextInput
          style={styles.input}
          value={destination}
          onChangeText={(t) => setDestination(t.toUpperCase())}
          placeholder="NRT"
          placeholderTextColor={Colors.gray[500]}
          maxLength={3}
          autoCapitalize="characters"
        />

        <Text style={styles.label}>DATE</Text>
        <TextInput
          style={styles.input}
          value={date}
          onChangeText={setDate}
          placeholder="2025-08-01"
          placeholderTextColor={Colors.gray[500]}
        />

        <TouchableOpacity
          style={[styles.crazyToggle, crazyMode && styles.crazyActive]}
          onPress={() => setCrazyMode(!crazyMode)}
        >
          <Text style={[styles.crazyText, crazyMode && styles.crazyTextActive]}>
            {crazyMode ? "CRAZY MODE ON" : "Enable Crazy Mode"}
          </Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.button, isSearching && styles.buttonDisabled]}
        onPress={handleSearch}
        disabled={isSearching}
      >
        {isSearching ? (
          <ActivityIndicator color={Colors.white} />
        ) : (
          <Text style={styles.buttonText}>HACK IT</Text>
        )}
      </TouchableOpacity>

      <Text style={styles.hint}>
        Searches 20 hacking methods simultaneously.{"\n"}
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
  label: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.gray[300],
    letterSpacing: 1.5,
    marginBottom: Spacing.xs,
    marginTop: Spacing.sm,
  },
  input: {
    backgroundColor: Colors.navy[700],
    color: Colors.white,
    fontSize: FontSize.lg,
    fontWeight: "600",
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
    letterSpacing: 2,
  },
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
