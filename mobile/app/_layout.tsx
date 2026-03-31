/**
 * Root layout — wraps all screens with QueryClientProvider and Zustand.
 * Uses Expo Router file-based routing.
 */
import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as SplashScreen from "expo-splash-screen";
import { Colors } from "../constants/theme";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: Colors.navy[900] },
            headerTintColor: Colors.white,
            headerTitleStyle: { fontWeight: "700" },
            contentStyle: { backgroundColor: Colors.navy[950] },
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="result/[id]"
            options={{ title: "Flight Details", presentation: "modal" }}
          />
        </Stack>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
