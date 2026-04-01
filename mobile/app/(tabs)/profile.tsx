/**
 * Profile tab — Avios balance & preferences.
 */
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from "react-native";
import { useState } from "react";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

export default function ProfileScreen() {
  const [avios, setAvios] = useState("");
  const [ppp, setPpp] = useState("1.0");

  function handleSave() {
    Alert.alert("Saved", "Your preferences have been saved.");
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Your Profile</Text>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>✈️  Avios / Points</Text>
        <Text style={styles.sectionDesc}>
          Enter your British Airways Avios balance so FlightHacker can show you reward flight options and calculate whether redeeming points beats buying cash fares.
        </Text>

        <Text style={styles.label}>AVIOS BALANCE</Text>
        <TextInput
          style={styles.input}
          value={avios}
          onChangeText={setAvios}
          placeholder="e.g. 50000"
          placeholderTextColor={Colors.gray[500]}
          keyboardType="numeric"
        />

        <Text style={styles.label}>PENCE PER AVIOS POINT</Text>
        <TextInput
          style={styles.input}
          value={ppp}
          onChangeText={setPpp}
          placeholder="1.0"
          placeholderTextColor={Colors.gray[500]}
          keyboardType="decimal-pad"
        />
        <Text style={styles.hint}>
          How much you value each Avios point. 1p = industry standard. Sweet spot redemptions often achieve 3–4p+. A higher number means you only redeem when it's an exceptional deal.
        </Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={handleSave}>
        <Text style={styles.buttonText}>SAVE</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.navy[950] },
  content: { padding: Spacing.lg },
  title: {
    fontSize: FontSize.xl,
    fontWeight: "700",
    color: Colors.white,
    marginBottom: Spacing.lg,
  },
  card: {
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: FontSize.md,
    fontWeight: "700",
    color: Colors.white,
    marginBottom: Spacing.xs,
  },
  sectionDesc: {
    fontSize: FontSize.sm,
    color: Colors.gray[400],
    lineHeight: 20,
    marginBottom: Spacing.md,
  },
  label: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.gray[300],
    letterSpacing: 1.5,
    marginBottom: Spacing.xs,
    marginTop: Spacing.md,
  },
  input: {
    backgroundColor: Colors.navy[700],
    color: Colors.white,
    fontSize: FontSize.md,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
  },
  hint: {
    fontSize: FontSize.xs,
    color: Colors.gray[500],
    marginTop: Spacing.xs,
    lineHeight: 17,
  },
  button: {
    backgroundColor: Colors.orange[500],
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: "center",
  },
  buttonText: {
    color: Colors.white,
    fontSize: FontSize.md,
    fontWeight: "800",
    letterSpacing: 2,
  },
});
