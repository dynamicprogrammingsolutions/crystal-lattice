export interface UiSchemaElement {
  ui_type?: string;
  // Config-oriented fields
  key?: string;
  type?: string;
  label?: string;
  icon?: string;
  description?: string;
  /** Keep the element visible but prevent configuration changes. */
  disabled?: boolean;
  options?: any;
  // Footer / status bar fields
  data?: string;
  template?: string;
  metadata?: Record<string, any>;
  /** Optional condition (all/any/not + path/eq|exists|empty) evaluated against message; when false, element is hidden. */
  condition?: unknown;
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
