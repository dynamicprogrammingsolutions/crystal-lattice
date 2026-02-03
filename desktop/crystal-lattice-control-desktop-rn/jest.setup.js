jest.mock(
  '@react-native-async-storage/async-storage',
  () => require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock('@crystal-lattice/frontend-sdk', () => ({
  CONNECTIONS_STORAGE_KEY: 'clc_connections_v1',
  loadConnections: async () => [],
  saveConnections: async () => {},
}));
