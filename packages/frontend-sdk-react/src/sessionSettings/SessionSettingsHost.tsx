import React, { Fragment, useMemo } from 'react';

import type {
  SessionSettingItem,
  SessionSettingsActions,
  SessionSettingsAfterItemRenderer,
  SessionSettingsFrameRenderer,
  SessionSettingsRenderers,
} from './types';

export interface SessionSettingsHostProps {
  items: SessionSettingItem[];
  actions: SessionSettingsActions;
  renderers: SessionSettingsRenderers;
  renderFrame?: SessionSettingsFrameRenderer;
  renderAfterItem?: SessionSettingsAfterItemRenderer;
}

export function SessionSettingsHost({
  items,
  actions,
  renderers,
  renderFrame,
  renderAfterItem,
}: SessionSettingsHostProps): React.JSX.Element {
  const content = useMemo(() => {
    const fallbackRenderer = renderers.fallback;

    return (Array.isArray(items) ? items : []).map((item) => {
      const typeRenderer = renderers[item.type];
      const renderer = typeRenderer ?? fallbackRenderer;

      if (renderer === fallbackRenderer) {
        return (
          <Fragment key={item.key}>
            {fallbackRenderer({ item, actions, renderFallback: () => null })}
            {renderAfterItem?.({ item })}
          </Fragment>
        );
      }

      const renderFallback = () =>
        fallbackRenderer({ item, actions, renderFallback: () => null });

      return (
        <Fragment key={item.key}>
          {renderer({ item, actions, renderFallback })}
          {renderAfterItem?.({ item })}
        </Fragment>
      );
    });
  }, [actions, items, renderAfterItem, renderers]);

  if (renderFrame) {
    return <>{renderFrame({ items, children: <>{content}</> })}</>;
  }

  return <>{content}</>;
}
