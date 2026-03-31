/**
 * Alerts tab — placeholder screen for price alert management.
 * Full implementation follows after the search flow is working.
 */
import { View, Text, StyleSheet } from "react-native";
import { Colors, Spacing, FontSize } from "../../constants/theme";

export default function AlertsScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Price Alerts</Text>
      <Text style={styles.sub}>
        Save a search and set a target price.{"\n"}
        We'll notify you via ntfy when it drops.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.navy[950],
    justifyContent: "center",
    alignItems: "center",
    padding: Spacing.xl,
  },
  title: {
    fontSize: FontSize.xl,
    fontWeight: "700",
    color: Colors.white,
    marginBottom: Spacing.md,
  },
  sub: {
    fontSize: FontSize.md,
    color: Colors.gray[500],
    textAlign: "center",
    lineHeight: 24,
  },
});
