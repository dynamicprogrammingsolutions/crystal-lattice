export type SessionActionKey = string;

export interface SessionActionDefinition {
  key: SessionActionKey;
  label: string;
  iconName: string;
  defaultPinned: boolean;
  order?: number;
}

export const SESSION_ACTIONS: Record<SessionActionKey, SessionActionDefinition> = {
  reload: {
    key: 'reload',
    label: 'Reload',
    iconName: 'refresh-ccw',
    defaultPinned: true,
    order: 0,
  },
  messageLimit: {
    key: 'messageLimit',
    label: 'Message limit',
    iconName: 'sliders',
    defaultPinned: false,
    order: 20,
  },
  agentSwitch: {
    key: 'agentSwitch',
    label: 'Agent switch',
    iconName: 'user',
    defaultPinned: false,
    order: 25,
  },
  debugEvents: {
    key: 'debugEvents',
    label: 'Debug events',
    iconName: 'activity',
    defaultPinned: false,
    order: 100,
  },
  settings: {
    key: 'settings',
    label: 'Settings',
    iconName: 'settings',
    defaultPinned: false,
    order: 90,
  },
  plugins: {
    key: 'plugins',
    label: 'Plugins',
    iconName: 'package',
    defaultPinned: false,
    order: 91,
  },
  snapshots: {
    key: 'snapshots',
    label: 'Snapshots',
    iconName: 'archive',
    defaultPinned: false,
    order: 92,
  },
};

export const ALL_SESSION_ACTIONS: SessionActionDefinition[] = Object.values(SESSION_ACTIONS);
