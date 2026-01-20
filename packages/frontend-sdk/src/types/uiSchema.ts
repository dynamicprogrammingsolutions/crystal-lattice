export interface UiSchemaElement {
  ui_type?: string;
  // Config-oriented fields
  key?: string;
  type?: string;
  label?: string;
  description?: string;
  options?: any;
  // Footer / status bar fields
  data?: string;
  template?: string;
  // Plugin / misc
  plugin?: string;
  [k: string]: any;
}

export interface ConfigSchemaEntry {
  key: string;
  plugin?: string;
  type?: string;
  default?: any;
  description?: string;
  [k: string]: any;
}
