export interface SessionPluginEntry {
  id: string;
  kind: 'providers' | 'extensions' | 'features' | 'tools' | (string & {});
  name?: string;
  class_path?: string;
  class_name?: string;
  enabled: boolean;
  source?: 'session' | 'agent' | 'implicit' | (string & {});
  active?: boolean;
  [k: string]: any;
}
