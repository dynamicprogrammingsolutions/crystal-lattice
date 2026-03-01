export interface SdkEvent {
  type: string;
  scopeKey: string;
  [key: string]: unknown;
}
