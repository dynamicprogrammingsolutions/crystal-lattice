export type ActionKey = string;

export interface ActionDefinition {
  key: ActionKey;
  label: string;
  order?: number;
  [k: string]: any;
}

export interface ActionsMenuModel<TDef extends ActionDefinition = ActionDefinition> {
  actionsByKey: Record<ActionKey, TDef>;
  orderedActions: TDef[];
  visiblePinned: TDef[];
  visibleOverflow: TDef[];
  isActionDisabled: (key: ActionKey) => boolean;
}

export interface ActionsMenuPinnedRenderParams<
  TDef extends ActionDefinition = ActionDefinition,
> {
  action: TDef;
  disabled: boolean;
  iconName: string | null;
  iconColor: string;
  onPress: () => void;
}
