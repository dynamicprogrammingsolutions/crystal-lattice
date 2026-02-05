import AsyncStorage from '@react-native-async-storage/async-storage';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

export const asyncStorageKeyValueStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};
