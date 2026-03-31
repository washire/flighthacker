/**
 * Profile tab — Avios balance, pence-per-point, ntfy topic.
 */
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import { useState } from "react";
import { Colors, Spacing, BorderRadius, FontSize } from "../../constants/theme";

export default function ProfileScreen() {
  const [avios, setAvios] = useState("");
  const [ppp, setPpp] = useState("1.0");
  const [ntfy, setNtfy] = useState("");

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Your Profile</Text>

      <View style={styles.card}>
        <Text style={styles.label}>AVIOS BALANCE</Text>
        <TextInput
          style={styles.input}
          value={avios}
          onChangeText={setAvios}
          placeholder="e.g. 50000"
          placeholderTextColor={Colors.gray[500]}
          keyboardType="numeric"
        />

        <Text style={styles.label}>PENCE PER POINT</Text>
        <TextInput
          style={styles.input}
          value={ppp}
          onChangeText={setPpp}
          placeholder="1.0"
          placeholderTextColor={Colors.gray[500]}
          keyboardType="decimal-pad"
        />
        <Text style={styles.hint}>
          Industry standard: 1p. Sweet spot redemptions: 3-4p+
        </Text>

        <Text style={styles.label}>NTFY TOPIC (for price alerts)</Text>
        <TextInput
          style={styles.input}
          value={ntfy}
          onChangeText={setNtfy}
          placeholder="my-flighthacker-alerts"
          placeholderTextColor={Colors.gray[500]}
          autoCapitalize="none"
        />
        <Text style={styles.hint}>
          Install ntfy.sh app → subscribe to this topic to get price alerts.
        </Text>
      </View>

      <TouchableOpacity style={styles.button}>
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
    lineHeight: 16,
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
