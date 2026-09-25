import {
  HumanTimeSpanUploader as SharedHumanTimeSpanUploader,
  type HumanTimeUploaderOptions as SharedHumanTimeUploaderOptions,
} from "@crystal-lattice/frontend-rn-components";

import {
  appendSpan,
  asyncStorageSpanCacheStore,
  type SpanCacheStore,
} from "./spanCache";

export {
  DEFAULT_CLOSE_DEBOUNCE_MS,
  DEFAULT_HUMAN_TIME_PLUGIN_ID,
  DEFAULT_TRANSIENT_RETRY_INTERVAL_MS,
  DEFAULT_UPLOAD_BATCH_LIMIT,
  HUMAN_TIME_ACTION_ID,
  HUMAN_TIME_ACTION_OWNER,
  isDefinitiveActionErrorType,
  isDefinitiveActionFailure,
  type FlushOutcome,
  type HumanTimeIngestionResult,
  type HumanTimeSpan,
  type HumanTimeUploadEvent,
} from "@crystal-lattice/frontend-rn-components";

export interface HumanTimeUploaderOptions extends Omit<
  SharedHumanTimeUploaderOptions,
  "store"
> {
  store?: SpanCacheStore;
}

export class HumanTimeSpanUploader extends SharedHumanTimeSpanUploader {
  constructor(options: HumanTimeUploaderOptions) {
    super({
      ...options,
      store: options.store ?? asyncStorageSpanCacheStore,
    });
  }
}

export { appendSpan };
