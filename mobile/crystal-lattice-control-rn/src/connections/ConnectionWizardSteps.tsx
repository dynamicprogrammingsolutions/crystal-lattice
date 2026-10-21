import React, { useMemo } from "react";
import {
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  type TextInputProps,
} from "react-native";
import { useTheme, type Theme } from "../theme";

export type ConnectionMethod =
  | "manual"
  | "discovery"
  | "bridge"
  | "cloud"
  | "embedded";
export interface DiscoveredService {
  name: string;
  host: string;
  port: number;
  addresses: string[];
}

export function useConnectionWizardStyles() {
  const theme = useTheme();
  return useMemo(() => createConnectionWizardStyles(theme), [theme]);
}

export function WizardPage({
  title,
  children,
  onCancel,
}: {
  title: string;
  children: React.ReactNode;
  onCancel: () => void;
}) {
  const styles = useConnectionWizardStyles();
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.title}>{title}</Text>
      {children}
      <WizardButton
        label="Cancel"
        onPress={onCancel}
        secondary
        testID="connection-wizard-cancel"
      />
    </ScrollView>
  );
}

export function WizardButton({
  label,
  description,
  onPress,
  secondary = false,
  disabled = false,
  testID,
}: {
  label: string;
  description?: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  testID?: string;
}) {
  const styles = useConnectionWizardStyles();
  return (
    <TouchableOpacity
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={[
        styles.button,
        secondary ? styles.secondaryButton : styles.primaryButton,
      ]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={secondary ? styles.buttonTextSecondary : styles.buttonText}>
        {label}
      </Text>
      {description ? (
        <Text style={styles.methodDescription}>{description}</Text>
      ) : null}
    </TouchableOpacity>
  );
}

export function WizardInput(props: TextInputProps) {
  const styles = useConnectionWizardStyles();
  return (
    <TextInput
      {...props}
      style={styles.input}
      autoCapitalize="none"
      autoCorrect={false}
    />
  );
}

export function ConnectionMethodStep({
  onSelect,
  onCancel,
}: {
  onSelect: (method: ConnectionMethod) => void;
  onCancel: () => void;
}) {
  const styles = useConnectionWizardStyles();
  const links = [
    [
      "Privacy Policy",
      "https://crystallattice.dev/privacy",
      "privacy-policy-link",
    ],
    ["Support", "https://crystallattice.dev/support", "support-link"],
  ];
  return (
    <WizardPage title="Select Connection Method" onCancel={onCancel}>
      <WizardButton
        testID="connection-method-manual"
        label="Manual Address"
        description="Enter IP address and port"
        onPress={() => onSelect("manual")}
      />
      <WizardButton
        testID="connection-method-discovery"
        label="Automatic Discovery"
        description="Find services via Bonjour"
        onPress={() => onSelect("discovery")}
      />
      <WizardButton
        testID="connection-method-bridge"
        label="Bridge Service"
        description="Connect via bridge server"
        onPress={() => onSelect("bridge")}
      />
      <WizardButton
        testID="connection-method-cloud"
        label="Cloud Agent Link"
        description="Paste a cloud session connection link"
        onPress={() => onSelect("cloud")}
      />
      <View style={styles.legalLinks}>
        {links.map(([label, url, id]) => (
          <TouchableOpacity
            key={id}
            accessibilityRole="link"
            testID={id}
            onPress={() => {
              void Linking.openURL(url).catch(() =>
                Alert.alert(
                  "Unable to Open Link",
                  `Please open ${url} in your browser.`
                )
              );
            }}
          >
            <Text style={styles.legalLinkText}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </WizardPage>
  );
}

export function ManualConnectionStep({
  host,
  port,
  onHost,
  onPort,
  onConnect,
  onCancel,
  loading,
}: {
  host: string;
  port: string;
  onHost: (value: string) => void;
  onPort: (value: string) => void;
  onConnect: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  return (
    <WizardPage title="Manual Connection" onCancel={onCancel}>
      <WizardInput
        testID="manual-host-input"
        placeholder="Host (e.g., 192.168.1.100)"
        value={host}
        onChangeText={onHost}
      />
      <WizardInput
        testID="manual-port-input"
        placeholder="Port (e.g., 8080)"
        value={port}
        onChangeText={onPort}
        keyboardType="number-pad"
      />
      <WizardButton
        testID="manual-connect-button"
        label={loading ? "Connecting..." : "Connect"}
        onPress={onConnect}
        disabled={loading}
      />
    </WizardPage>
  );
}

export function DiscoveryConnectionStep({
  searching,
  services,
  onConnect,
  onCancel,
  loading,
}: {
  searching: boolean;
  services: readonly DiscoveredService[];
  onConnect: (service: DiscoveredService) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const styles = useConnectionWizardStyles();
  return (
    <WizardPage title="Service Discovery" onCancel={onCancel}>
      <Text style={styles.infoText}>
        {searching ? "Searching..." : "Not searching"}
      </Text>
      {services.length ? (
        <Text style={styles.sectionTitle}>
          Found {services.length} service(s)
        </Text>
      ) : null}
      {services.map((service, index) => (
        <TouchableOpacity
          key={`${service.name}-${index}`}
          style={styles.serviceItem}
          onPress={() => onConnect(service)}
          disabled={loading}
        >
          <Text style={styles.serviceName}>{service.name}</Text>
          <Text style={styles.serviceDetails}>
            {service.host}:{service.port}
          </Text>
        </TouchableOpacity>
      ))}
      {searching && !services.length ? (
        <Text style={styles.infoText}>Searching for services...</Text>
      ) : null}
    </WizardPage>
  );
}

export function CloudConnectionStep({
  link,
  onLink,
  onConnect,
  onCancel,
  loading,
}: {
  link: string;
  onLink: (value: string) => void;
  onConnect: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  return (
    <WizardPage title="Cloud Agent Link" onCancel={onCancel}>
      <WizardInput
        testID="cloud-connection-link-input"
        placeholder="crystal-lattice-cloud://connect?..."
        value={link}
        onChangeText={onLink}
      />
      <WizardButton
        testID="cloud-connect-button"
        label={loading ? "Connecting..." : "Connect to Cloud Agent"}
        onPress={onConnect}
        disabled={loading}
      />
    </WizardPage>
  );
}

export function EmbeddedConnectionStep({
  proxyUrl,
  model,
  apiKey,
  hasKey,
  onProxyUrl,
  onModel,
  onApiKey,
  onConnect,
  onCancel,
  loading,
}: {
  proxyUrl: string;
  model: string;
  apiKey: string;
  hasKey: boolean;
  onProxyUrl: (value: string) => void;
  onModel: (value: string) => void;
  onApiKey: (value: string) => void;
  onConnect: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  return (
    <WizardPage title="Local agent" onCancel={onCancel}>
      <WizardInput
        testID="embedded-proxy-url-input"
        placeholder="Proxy URL"
        value={proxyUrl}
        onChangeText={onProxyUrl}
      />
      <WizardInput
        testID="embedded-model-input"
        placeholder="Model"
        value={model}
        onChangeText={onModel}
      />
      <WizardInput
        testID="embedded-api-key-input"
        placeholder={
          hasKey ? "API key saved — leave blank to keep it" : "Proxy API key"
        }
        value={apiKey}
        onChangeText={onApiKey}
        secureTextEntry
      />
      <WizardButton
        testID="embedded-connect-button"
        label={loading ? "Starting..." : "Start Local agent"}
        onPress={onConnect}
        disabled={loading}
      />
    </WizardPage>
  );
}

export const createConnectionWizardStyles = (theme: Theme) =>
  StyleSheet.create({
    scroll: { flexShrink: 1 },
    container: { padding: 16 },
    title: {
      fontSize: 24,
      fontWeight: "bold",
      marginBottom: 24,
      textAlign: "center",
      color: theme.text,
    },
    button: {
      paddingHorizontal: 20,
      paddingVertical: 12,
      borderRadius: 8,
      alignItems: "center",
      marginBottom: 12,
    },
    primaryButton: { backgroundColor: theme.primary },
    secondaryButton: { backgroundColor: theme.surfaceAlt, marginTop: 8 },
    buttonText: { color: theme.textOnPrimary, fontSize: 16, fontWeight: "600" },
    buttonTextSecondary: { color: theme.text, fontSize: 16, fontWeight: "600" },
    methodDescription: {
      color: theme.textOnPrimary,
      fontSize: 12,
      marginTop: 4,
      opacity: 0.8,
    },
    legalLinks: {
      flexDirection: "row",
      justifyContent: "center",
      gap: 16,
      marginTop: 8,
    },
    legalLinkText: { color: theme.primary, fontSize: 14, fontWeight: "600" },
    input: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
      fontSize: 16,
      color: theme.text,
    },
    savedBridgeRow: { flexDirection: "row", alignItems: "center", gap: 12 },
    savedBridgeMain: { flex: 1, paddingVertical: 8 },
    savedBridgeRemove: { padding: 10 },
    section: { marginTop: 16 },
    sectionTitle: {
      fontSize: 18,
      fontWeight: "600",
      marginBottom: 8,
      color: theme.text,
    },
    serviceItem: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    serviceName: {
      fontSize: 16,
      fontWeight: "600",
      marginBottom: 4,
      color: theme.text,
    },
    serviceDetails: { fontSize: 12, color: theme.textSecondary },
    infoText: {
      fontSize: 14,
      color: theme.textSecondary,
      textAlign: "center",
      fontStyle: "italic",
      marginVertical: 16,
    },
  });
