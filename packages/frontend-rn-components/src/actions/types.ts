export type ActionKey = string;

export interface ActionDefinition {
  key: ActionKey;
  label: string;
  [k: string]: any;
}

export interface ActionsMenuModel<TDef extends ActionDefinition = ActionDefinition> {
  actionsByKey: Record<ActionKey, TDef>;
  orderedActions: TDef[];
  visiblePinned: TDef[];
  visibleOverflow: TDef[];
  isActionDisabled: (key: ActionKey) => boolean;
}
