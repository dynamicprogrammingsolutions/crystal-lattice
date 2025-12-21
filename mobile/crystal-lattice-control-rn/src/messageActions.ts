export type MessageActionKey = 'delete' | 'modify' | 'fork';

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
  delete: {
    key: 'delete',
    label: 'Delete',
    iconName: 'trash-2',
    defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
    allowedRoles: ['user', 'assistant', 'system', 'tool'],
  },
  modify: {
    key: 'modify',
    label: 'Modify',
    iconName: 'edit-3',
    defaultPinnedRoles: ['user', 'assistant', 'system'],
    allowedRoles: ['user', 'assistant', 'system'],
  },
  fork: {
    key: 'fork',
    label: 'Fork',
    iconName: 'git-branch',
    defaultPinnedRoles: ['user', 'assistant'],
    allowedRoles: ['user', 'assistant', 'system', 'tool'],
  },
};

export const ALL_MESSAGE_ACTIONS: MessageActionDefinition[] = Object.values(MESSAGE_ACTIONS);
