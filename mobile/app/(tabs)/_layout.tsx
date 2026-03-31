import { Tabs } from "expo-router";
import { Colors } from "../../constants/theme";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: Colors.navy[900],
          borderTopColor: Colors.navy[700],
        },
        tabBarActiveTintColor: Colors.orange[400],
        tabBarInactiveTintColor: Colors.gray[500],
        headerStyle: { backgroundColor: Colors.navy[900] },
        headerTintColor: Colors.white,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Search", tabBarLabel: "Search" }}
      />
      <Tabs.Screen
        name="results"
        options={{ title: "Results", tabBarLabel: "Results" }}
      />
      <Tabs.Screen
        name="alerts"
        options={{ title: "Alerts", tabBarLabel: "Alerts" }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: "Profile", tabBarLabel: "Profile" }}
      />
    </Tabs>
  );
}
