export type MessageActionKey = string;

export interface MessageActionDefinition {
  key: MessageActionKey;
  label: string;
  iconName: string;
  // Roles for which this action is pinned by default (e.g. 'user', 'assistant', 'system', 'tool').
  defaultPinnedRoles: string[];
  // Roles where this action is allowed / should be offered.
  allowedRoles: string[];
}

export const MESSAGE_ACTIONS: Record<MessageActionKey, MessageActionDefinition> = {
  modify: {
    key: 'modify',
    label: 'Modify',
    iconName: 'edit-3',
    defaultPinnedRoles: ['user', 'assistant', 'system'],
    allowedRoles: ['user', 'assistant', 'system'],
  },
  toggleMarkdown: {
    key: 'toggleMarkdown',
    label: 'Toggle markdown',
    iconName: 'code',
    defaultPinnedRoles: ['user', 'assistant'],
    allowedRoles: ['user', 'assistant'],
  },
  copy: {
    key: 'copy',
    label: 'Copy message',
    iconName: 'copy',
    defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
    allowedRoles: ['user', 'assistant', 'system', 'tool'],
  },
};

export const ALL_MESSAGE_ACTIONS: MessageActionDefinition[] = Object.values(MESSAGE_ACTIONS);
