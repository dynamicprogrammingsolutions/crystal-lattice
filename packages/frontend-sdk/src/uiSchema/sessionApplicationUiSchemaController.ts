import type { AgentBackend } from '../backend/backend';
import type { ApplicationUiElement } from '../types/plugins';
import { SimpleSubscribable } from '../util/subscribable';

export interface SessionApplicationUiSchemaControllerState {
  loading: boolean;
  error: string | null;
  elements: ApplicationUiElement[];
}

const EMPTY_STATE: SessionApplicationUiSchemaControllerState = {
  loading: false,
  error: null,
  elements: [],
};

const CACHE: Map<string, ApplicationUiElement[] | null | undefined> = new Map();

export class SessionApplicationUiSchemaController extends SimpleSubscribable<SessionApplicationUiSchemaControllerState> {
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

  /** Update state and cache from a fresh fetch without calling the backend. */
  setElements(elements: ApplicationUiElement[]): void {
    const list = Array.isArray(elements) ? elements : [];
    CACHE.set(this.buildCacheKey(), list);
    this.setSnapshot({ loading: false, error: null, elements: list });
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
      const els = await this.backend.getSessionApplicationUiSchema(this.sessionId);
      const elements = Array.isArray(els) ? els : [];
      CACHE.set(this.buildCacheKey(), elements);
      this.setSnapshot({ loading: false, error: null, elements });
    } catch (err: any) {
      CACHE.set(this.buildCacheKey(), null);
      this.setSnapshot({ loading: false, error: err?.message || 'Failed to load', elements: [] });
    }
  }
}