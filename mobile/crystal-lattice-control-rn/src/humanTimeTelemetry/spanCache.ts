import AsyncStorage from "@react-native-async-storage/async-storage";

import {
  HUMAN_TIME_SPANS_SOFT_CAP,
  HUMAN_TIME_SPANS_STORAGE_KEY,
  appendHumanTimeSpan,
  loadHumanTimeSpans,
  removeFirstHumanTimeSpans,
  removeHumanTimeSpans,
  type HumanTimeSpan,
  type SpanCacheStore,
} from "@crystal-lattice/frontend-rn-components";

export type { SpanCacheStore };
export { HUMAN_TIME_SPANS_SOFT_CAP, HUMAN_TIME_SPANS_STORAGE_KEY };

export const asyncStorageSpanCacheStore: SpanCacheStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};

export function appendSpan(
  connectionId: string,
  span: HumanTimeSpan,
  store: SpanCacheStore = asyncStorageSpanCacheStore,
): Promise<boolean> {
  return appendHumanTimeSpan(connectionId, span, store);
}

export function loadSpans(
  connectionId: string,
  store: SpanCacheStore = asyncStorageSpanCacheStore,
): Promise<HumanTimeSpan[]> {
  return loadHumanTimeSpans(connectionId, store);
}

export function removeFirstSpans(
  connectionId: string,
  count: number,
  store: SpanCacheStore = asyncStorageSpanCacheStore,
): Promise<void> {
  return removeFirstHumanTimeSpans(connectionId, count, store);
}

export function removeSpans(
  connectionId: string,
  confirmed: HumanTimeSpan[],
  store: SpanCacheStore = asyncStorageSpanCacheStore,
): Promise<void> {
  return removeHumanTimeSpans(connectionId, confirmed, store);
}
