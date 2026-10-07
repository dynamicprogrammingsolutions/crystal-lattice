import React from "react";
import { Text, TouchableOpacity, View } from "react-native";
import type {
  BridgeServer,
  BridgeTransportMode,
} from "@crystal-lattice/frontend-sdk";
import {
  WizardButton,
  WizardInput,
  WizardPage,
  useConnectionWizardStyles,
} from "./ConnectionWizardSteps";

interface BridgeConnectionStepProps {
  url: string;
  mode: BridgeTransportMode;
  servers: readonly BridgeServer[];
  connected: boolean;
  selectedServer: BridgeServer | null;
  code: string;
  loading: boolean;
  onUrl: (value: string) => void;
  onMode: (mode: BridgeTransportMode) => void;
  onCode: (value: string) => void;
  onConnect: () => void;
  onTest: () => void;
  onPair: (server: BridgeServer) => void;
  onSubmit: () => void;
  onCancelPairing: () => void;
  onCancel: () => void;
}

export default function BridgeConnectionStep(props: BridgeConnectionStepProps) {
  const styles = useConnectionWizardStyles();
  return (
    <WizardPage title="Bridge Connection" onCancel={props.onCancel}>
      {!props.connected ? (
        <>
          <Text style={styles.infoText}>
            For testing on a physical device, use your computer's IP address
            (not localhost).
          </Text>
          <Text style={styles.infoText}>
            Example: ws://192.168.1.100:4000/ws/websocket
          </Text>
          <WizardInput
            testID="bridge-url-input"
            placeholder="Bridge URL (e.g., ws://192.168.1.100:4000/ws/websocket)"
            value={props.url}
            onChangeText={props.onUrl}
          />
          <Text style={styles.bridgeModeLabel}>Transport (experimental)</Text>
          <View style={styles.bridgeModeSelector}>
            {(
              [
                ["websocket", "WebSocket"],
                ["http", "HTTP"],
                ["hybrid", "Hybrid"],
              ] as const
            ).map(([mode, label]) => (
              <TouchableOpacity
                key={mode}
                testID={`bridge-transport-mode-${mode}`}
                accessibilityRole="button"
                accessibilityLabel={`${label} bridge transport${
                  props.mode === mode ? " selected" : ""
                }`}
                accessibilityState={{ selected: props.mode === mode }}
                style={[
                  styles.bridgeModeButton,
                  props.mode === mode && styles.bridgeModeButtonSelected,
                ]}
                onPress={() => props.onMode(mode)}
                disabled={props.loading}
              >
                <Text
                  style={[
                    styles.bridgeModeButtonText,
                    props.mode === mode && styles.bridgeModeButtonTextSelected,
                  ]}
                >
                  {label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.bridgeModeHint}>
            WebSocket is the stable default. Hybrid keeps event polling on
            WebSocket and sends all other requests over HTTP.
          </Text>
          <WizardButton
            testID="bridge-connect-button"
            label={props.loading ? "Connecting..." : "Connect to Bridge"}
            onPress={props.onConnect}
            disabled={props.loading}
          />
          <WizardButton
            label="Test Connectivity"
            onPress={props.onTest}
            disabled={props.loading || !props.url}
            secondary
          />
        </>
      ) : null}
      {props.connected && !props.selectedServer ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Available Servers ({props.servers.length})
          </Text>
          {props.servers.map((server) => (
            <TouchableOpacity
              key={server.server_id}
              style={styles.serviceItem}
              onPress={() => props.onPair(server)}
              disabled={props.loading}
            >
              <Text style={styles.serviceName}>{server.display_name}</Text>
              <Text style={styles.serviceDetails}>{server.computer_name}</Text>
              <Text style={styles.serviceDetails}>ID: {server.server_id}</Text>
              {server.location ? (
                <Text style={styles.serviceDetails}>{server.location}</Text>
              ) : null}
            </TouchableOpacity>
          ))}
        </View>
      ) : null}
      {props.selectedServer ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Pairing with {props.selectedServer.display_name}
          </Text>
          <Text style={styles.infoText}>
            Check the server terminal for the 6-digit pairing code
          </Text>
          <WizardInput
            testID="bridge-pairing-code-input"
            placeholder="Enter 6-digit code"
            value={props.code}
            onChangeText={props.onCode}
            keyboardType="number-pad"
            maxLength={6}
          />
          <WizardButton
            testID="bridge-submit-pairing"
            label={props.loading ? "Pairing..." : "Submit Code"}
            onPress={props.onSubmit}
            disabled={props.loading}
          />
          <WizardButton
            label="Cancel"
            onPress={props.onCancelPairing}
            secondary
          />
        </View>
      ) : null}
    </WizardPage>
  );
}
