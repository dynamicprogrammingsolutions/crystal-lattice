export interface SessionSummaryPresentation {
  title: string;
  subtitle: string | null;
  meta: string | null;
}

export interface SessionSummary {
  session_id: string;
  modified: number;
  preview: string;
  metadata?: Record<string, any>;
  presentation?: SessionSummaryPresentation;
}
