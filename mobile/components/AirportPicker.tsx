import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Modal,
  FlatList,
  StyleSheet,
} from "react-native";
import { searchOptions, type Airport, type CityGroup, type AirportOption } from "../data/airports";
import { Colors, Spacing, BorderRadius, FontSize } from "../constants/theme";

export interface AirportSelection {
  iata: string;           // primary IATA (used as origin/destination)
  airports: string[];     // all IATAs (>1 means city mode)
  city: string;           // display city name
  label: string;          // full display label
}

interface Props {
  label: string;
  value: AirportSelection | null;
  onChange: (selection: AirportSelection) => void;
}

export function AirportPicker({ label, value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const results = searchOptions(query);

  function selectOption(option: AirportOption) {
    if (option.type === "city") {
      const g = option as CityGroup;
      onChange({
        iata: g.airports[0],
        airports: g.airports,
        city: g.city,
        label: g.label,
      });
    } else {
      const a = option as Airport;
      onChange({
        iata: a.iata,
        airports: [a.iata],
        city: a.city,
        label: `${a.iata} — ${a.city}, ${a.name}`,
      });
    }
    setQuery("");
    setOpen(false);
  }

  const displayText = value
    ? value.airports.length > 1
      ? `${value.city} (${value.airports.slice(0, 3).join(", ")}${value.airports.length > 3 ? " +" + (value.airports.length - 3) : ""})`
      : `${value.iata} — ${value.city}`
    : null;

  return (
    <>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity style={styles.input} onPress={() => setOpen(true)}>
        {value ? (
          <View>
            <Text style={styles.valueText}>{displayText}</Text>
            {value.airports.length > 1 && (
              <Text style={styles.cityModeTag}>All airports · city search</Text>
            )}
          </View>
        ) : (
          <Text style={styles.placeholderText}>Search city or airport…</Text>
        )}
      </TouchableOpacity>

      <Modal visible={open} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>{label}</Text>
            <TouchableOpacity onPress={() => { setQuery(""); setOpen(false); }}>
              <Text style={styles.cancel}>Cancel</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.searchInput}
            value={query}
            onChangeText={setQuery}
            placeholder="City, airport or code…"
            placeholderTextColor={Colors.gray[500]}
            autoFocus
            autoCorrect={false}
            autoCapitalize="none"
          />

          <FlatList
            data={results}
            keyExtractor={(item) =>
              item.type === "city" ? `city-${(item as CityGroup).city}` : (item as Airport).iata
            }
            keyboardShouldPersistTaps="handled"
            renderItem={({ item }) => {
              if (item.type === "city") {
                const g = item as CityGroup;
                return (
                  <TouchableOpacity style={styles.cityRow} onPress={() => selectOption(g)}>
                    <View style={styles.cityBadge}>
                      <Text style={styles.cityBadgeText}>ALL</Text>
                    </View>
                    <View style={styles.rowInfo}>
                      <Text style={styles.city}>{g.city}</Text>
                      <Text style={styles.airportName}>
                        {g.airports.join(" · ")} — searches all combinations
                      </Text>
                    </View>
                    <Text style={styles.flag}>{getFlagEmoji(g.country)}</Text>
                  </TouchableOpacity>
                );
              }
              const a = item as Airport;
              return (
                <TouchableOpacity style={styles.row} onPress={() => selectOption(a)}>
                  <View style={styles.iataBox}>
                    <Text style={styles.iata}>{a.iata}</Text>
                  </View>
                  <View style={styles.rowInfo}>
                    <Text style={styles.city}>{a.city}</Text>
                    <Text style={styles.airportName}>{a.name}</Text>
                  </View>
                  <Text style={styles.flag}>{getFlagEmoji(a.country)}</Text>
                </TouchableOpacity>
              );
            }}
            ListEmptyComponent={
              <Text style={styles.noResults}>
                {query.length >= 2 ? "No airports found" : "Type a city name or airport code"}
              </Text>
            }
          />
        </View>
      </Modal>
    </>
  );
}

function getFlagEmoji(countryCode: string): string {
  const base = 0x1F1E6 - 65;
  const chars = countryCode
    .toUpperCase()
    .split("")
    .map((c) => String.fromCodePoint(base + c.charCodeAt(0)));
  return chars.join("");
}

const styles = StyleSheet.create({
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
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
  },
  valueText: {
    color: Colors.white,
    fontSize: FontSize.md,
    fontWeight: "600",
  },
  cityModeTag: {
    color: Colors.teal[400],
    fontSize: FontSize.xs,
    marginTop: 2,
  },
  placeholderText: {
    color: Colors.gray[500],
    fontSize: FontSize.md,
  },
  modal: {
    flex: 1,
    backgroundColor: Colors.navy[950],
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: Spacing.lg,
    paddingTop: Spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: Colors.navy[700],
  },
  modalTitle: {
    fontSize: FontSize.lg,
    fontWeight: "700",
    color: Colors.white,
  },
  cancel: {
    color: Colors.orange[400],
    fontSize: FontSize.md,
  },
  searchInput: {
    backgroundColor: Colors.navy[800],
    color: Colors.white,
    fontSize: FontSize.md,
    padding: Spacing.md,
    margin: Spacing.md,
    borderRadius: BorderRadius.md,
  },
  cityRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: Spacing.md,
    paddingHorizontal: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: Colors.navy[800],
    gap: Spacing.md,
    backgroundColor: `${Colors.teal[500]}10`,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    padding: Spacing.md,
    paddingHorizontal: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: Colors.navy[800],
    gap: Spacing.md,
  },
  cityBadge: {
    backgroundColor: Colors.teal[500],
    borderRadius: BorderRadius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    minWidth: 50,
    alignItems: "center",
  },
  cityBadgeText: {
    color: Colors.white,
    fontSize: FontSize.xs,
    fontWeight: "800",
    letterSpacing: 1,
  },
  iataBox: {
    backgroundColor: Colors.navy[700],
    borderRadius: BorderRadius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    minWidth: 50,
    alignItems: "center",
  },
  iata: {
    color: Colors.orange[400],
    fontSize: FontSize.md,
    fontWeight: "800",
    letterSpacing: 1,
  },
  rowInfo: { flex: 1 },
  city: {
    color: Colors.white,
    fontSize: FontSize.md,
    fontWeight: "600",
  },
  airportName: {
    color: Colors.gray[400],
    fontSize: FontSize.xs,
    marginTop: 2,
  },
  flag: { fontSize: 20 },
  noResults: {
    color: Colors.gray[500],
    textAlign: "center",
    marginTop: Spacing.xl,
    fontSize: FontSize.sm,
  },
});
