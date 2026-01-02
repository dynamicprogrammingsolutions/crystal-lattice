import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface UsePersistentPinnedActionsResult<T extends string> {
  pinned: T[];
  setPinned: Dispatch<SetStateAction<T[]>>;
}

export function usePersistentPinnedActions<T extends string>(
  storageKey: string,
  initialPinned: T[],
): UsePersistentPinnedActionsResult<T> {
  const [pinned, setPinned] = useState<T[]>(initialPinned);

  useEffect(() => {
    const loadPinned = async () => {
      try {
        const raw = await AsyncStorage.getItem(storageKey);
        if (!raw) return;
        try {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            const valid = parsed.filter((key: any) => typeof key === 'string');
            if (valid.length > 0 || parsed.length === 0) {
              setPinned(valid as T[]);
            }
          }
        } catch (err) {
          console.log(`Failed to parse stored pinned actions for ${storageKey}`, err);
        }
      } catch (err) {
        console.log(`Failed to load pinned actions for ${storageKey}`, err);
      }
    };

    loadPinned();
  }, [storageKey]);

  useEffect(() => {
    const savePinned = async () => {
      try {
        await AsyncStorage.setItem(storageKey, JSON.stringify(pinned));
      } catch (err) {
        console.log(`Failed to save pinned actions for ${storageKey}`, err);
      }
    };

    savePinned();
  }, [storageKey, pinned]);

  return { pinned, setPinned };
}
