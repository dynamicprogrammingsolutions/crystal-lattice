export type SessionActionKey = string;

export interface SessionActionDefinition {
  key: SessionActionKey;
  label: string;
  iconName: string;
  defaultPinned: boolean;
}

export const SESSION_ACTIONS: Record<SessionActionKey, SessionActionDefinition> = {
  reload: {
    key: 'reload',
    label: 'Reload',
    iconName: 'refresh-ccw',
    defaultPinned: true,
  },
  resend: {
    key: 'resend',
    label: 'Resend',
    iconName: 'repeat',
    defaultPinned: true,
  },
  messageLimit: {
    key: 'messageLimit',
    label: 'Message limit',
    iconName: 'sliders',
    defaultPinned: false,
  },
  deleteRange: {
    key: 'deleteRange',
    label: 'Delete range',
    iconName: 'trash-2',
    defaultPinned: false,
  },
  agentSwitch: {
    key: 'agentSwitch',
    label: 'Agent switch',
    iconName: 'user',
    defaultPinned: false,
  },
  debugEvents: {
    key: 'debugEvents',
    label: 'Debug events',
    iconName: 'activity',
    defaultPinned: false,
  },
  settings: {
    key: 'settings',
    label: 'Settings',
    iconName: 'settings',
    defaultPinned: false,
  },
};

export const ALL_SESSION_ACTIONS: SessionActionDefinition[] = Object.values(SESSION_ACTIONS);
