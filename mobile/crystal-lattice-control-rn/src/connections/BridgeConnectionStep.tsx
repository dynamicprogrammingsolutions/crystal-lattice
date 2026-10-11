import React, { useState } from "react";
import { Text, TouchableOpacity, View } from "react-native";
import Icon from "react-native-vector-icons/Feather";
import { useTheme } from "../theme";
import type {
  BridgeServer,
  SavedBridgeUrl,
} from "@crystal-lattice/frontend-sdk";
import {
  WizardButton,
  WizardInput,
  WizardPage,
  useConnectionWizardStyles,
} from "./ConnectionWizardSteps";

interface BridgeConnectionStepProps {
  url: string;
  savedBridges: readonly SavedBridgeUrl[];
  servers: readonly BridgeServer[];
  connected: boolean;
  selectedServer: BridgeServer | null;
  code: string;
  loading: boolean;
  storageError?: string;
  onUrl: (value: string) => void;
  onCode: (value: string) => void;
  onConnect: () => void;
  onSelectSaved: (url: string) => void;
  onRemoveSaved: (url: string) => void;
  onTest: () => void;
  onPair: (server: BridgeServer) => void;
  onSubmit: () => void;
  onCancelPairing: () => void;
  onCancel: () => void;
}

export default function BridgeConnectionStep(props: BridgeConnectionStepProps) {
  const styles = useConnectionWizardStyles();
  const theme = useTheme();
  const [adding, setAdding] = useState(false);
  return (
    <WizardPage title="Bridge Connection" onCancel={props.onCancel}>
      {!props.connected ? (
        <>
          <Text style={styles.sectionTitle}>Saved Bridges</Text>
          {props.storageError ? <Text style={styles.infoText}>{props.storageError}</Text> : null}
          {props.savedBridges.length === 0 ? (
            <Text style={styles.infoText}>No saved bridges yet.</Text>
          ) : null}
          {props.savedBridges.map((bridge) => (
            <View key={bridge.url} style={[styles.serviceItem, styles.savedBridgeRow]}>
              <TouchableOpacity
                testID={`saved-bridge-open-${bridge.url}`}
                accessibilityRole="button"
                accessibilityLabel={`Connect to ${bridge.label ?? bridge.url}`}
                style={styles.savedBridgeMain}
                onPress={() => props.onSelectSaved(bridge.url)}
                disabled={props.loading}
              >
                {bridge.label ? <Text style={styles.serviceName}>{bridge.label}</Text> : null}
                <Text style={styles.serviceDetails}>{bridge.url}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                testID={`saved-bridge-remove-${bridge.url}`}
                accessibilityRole="button"
                accessibilityLabel={`Remove ${bridge.label ?? bridge.url}`}
                style={styles.savedBridgeRemove}
                onPress={() => props.onRemoveSaved(bridge.url)}
                disabled={props.loading}
              >
                <Icon name="trash-2" size={20} color={theme.danger} />
              </TouchableOpacity>
            </View>
          ))}
          <WizardButton
            testID="bridge-add-new"
            label="Add New Bridge"
            onPress={() => setAdding(true)}
            disabled={props.loading}
            secondary
          />
          {adding ? (
            <>
              <WizardInput
                testID="bridge-url-input"
                placeholder="Bridge URL"
                value={props.url}
                onChangeText={props.onUrl}
              />
              <WizardButton
                testID="bridge-connect-button"
                label={props.loading ? "Connecting..." : "Connect to Bridge"}
                onPress={props.onConnect}
                disabled={props.loading || !props.url}
              />
              <WizardButton
                label="Test Connectivity"
                onPress={props.onTest}
                disabled={props.loading || !props.url}
                secondary
              />
            </>
          ) : null}
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
              testID={`bridge-server-${server.server_id}`}
              accessibilityRole="button"
              accessibilityLabel={`Pair with ${server.display_name}`}
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
