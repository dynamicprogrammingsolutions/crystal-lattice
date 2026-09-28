import AsyncStorage from '@react-native-async-storage/async-storage';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

export const asyncStorageKeyValueStore: KeyValueStore = {
  get: key => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: key => AsyncStorage.removeItem(key),
};

export function createNamespacedKeyValueStore(
  store: KeyValueStore,
  namespace: string,
): KeyValueStore {
  const keyFor = (key: string) => `${namespace}:${key}`;
  return {
    get: key => store.get(keyFor(key)),
    set: (key, value) => store.set(keyFor(key), value),
    delete: key => store.delete(keyFor(key)),
  };
}
