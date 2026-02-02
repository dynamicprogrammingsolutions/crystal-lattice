import type { AgentBackend } from '../backend/backend';
import type { UiSchemaElement } from '../types/uiSchema';
import { SimpleSubscribable } from '../util/subscribable';

export interface SessionUiSchemaControllerState {
  loading: boolean;
  error: string | null;
  elements: UiSchemaElement[];
}

const EMPTY_STATE: SessionUiSchemaControllerState = {
  loading: false,
  error: null,
  elements: [],
};

const CACHE: Map<string, UiSchemaElement[] | null | undefined> = new Map();

export class SessionUiSchemaController extends SimpleSubscribable<SessionUiSchemaControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;
  private sessionId: string;

  constructor(options: {
    backend: AgentBackend | null;
    cacheKey: string;
    sessionId: string;
  }) {
    super(EMPTY_STATE);
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;
    this.sessionId = options.sessionId;

    const cached = CACHE.get(this.buildCacheKey());
    if (cached !== undefined) {
      this.setSnapshot({ loading: false, error: null, elements: cached || [] });
    }
  }

  private buildCacheKey(): string {
    return `${this.cacheKey}::${this.sessionId}`;
  }

  invalidate(): void {
    CACHE.delete(this.buildCacheKey());
  }

  async load(): Promise<void> {
    if (!this.backend) {
      this.setSnapshot(EMPTY_STATE);
      return;
    }

    const existing = CACHE.get(this.buildCacheKey());
    if (existing !== undefined) {
      this.setSnapshot({ loading: false, error: null, elements: existing || [] });
      return;
    }

    this.setSnapshot({ ...this.getSnapshot(), loading: true, error: null });
    try {
      const els = await this.backend.getSessionUiSchema(this.sessionId);
      const elements = Array.isArray(els) ? els : [];
      CACHE.set(this.buildCacheKey(), elements);
      this.setSnapshot({ loading: false, error: null, elements });
    } catch (err: any) {
      CACHE.set(this.buildCacheKey(), null);
      this.setSnapshot({ loading: false, error: err?.message || 'Failed to load', elements: [] });
    }
  }
}
