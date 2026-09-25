import type {
  HumanTimeDiagnosticEntry,
  HumanTimeSpan,
  HumanTimeUploadEvent,
} from '@crystal-lattice/frontend-rn-components';

export interface DesktopHumanTimeDiagnosticEntry
  extends HumanTimeDiagnosticEntry {
  connectionId: string;
}

export interface DesktopHumanTimeDiagnosticSpan {
  connectionId: string;
  span: HumanTimeSpan;
}

export interface DesktopHumanTimeDiagnosticUpload {
  connectionId: string;
  event: HumanTimeUploadEvent;
}

export interface DesktopHumanTimeDiagnostics {
  enabled: boolean;
  connectedConnectionCount: number;
  activityEventCount: number;
  openSpan: DesktopHumanTimeDiagnosticSpan | null;
  lastCollectedSpan: DesktopHumanTimeDiagnosticSpan | null;
  pendingCount: number;
  lastUpload: DesktopHumanTimeDiagnosticUpload | null;
  recentEntries: DesktopHumanTimeDiagnosticEntry[];
  collectionError: string | null;
}

export const EMPTY_DESKTOP_HUMAN_TIME_DIAGNOSTICS: DesktopHumanTimeDiagnostics =
  {
    enabled: false,
    connectedConnectionCount: 0,
    activityEventCount: 0,
    openSpan: null,
    lastCollectedSpan: null,
    pendingCount: 0,
    lastUpload: null,
    recentEntries: [],
    collectionError: null,
  };

type DiagnosticsListener = (snapshot: DesktopHumanTimeDiagnostics) => void;

let snapshot = EMPTY_DESKTOP_HUMAN_TIME_DIAGNOSTICS;
let controller: {
  refresh: () => Promise<void>;
  uploadNow: () => Promise<void>;
} | null = null;
const listeners = new Set<DiagnosticsListener>();

export const desktopHumanTimeDiagnosticsBridge = {
  getSnapshot(): DesktopHumanTimeDiagnostics {
    return snapshot;
  },

  publish(next: DesktopHumanTimeDiagnostics): void {
    snapshot = next;
    listeners.forEach(listener => {
      try {
        listener(next);
      } catch {}
    });
  },

  subscribe(listener: DiagnosticsListener): () => void {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  registerController(next: {
    refresh: () => Promise<void>;
    uploadNow: () => Promise<void>;
  }): () => void {
    controller = next;
    return () => {
      if (controller === next) {
        controller = null;
      }
    };
  },

  async refresh(): Promise<void> {
    await controller?.refresh();
  },

  async uploadNow(): Promise<void> {
    await controller?.uploadNow();
  },
};
