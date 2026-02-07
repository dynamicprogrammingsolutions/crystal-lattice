import React, { Fragment, useMemo } from 'react';

import type {
  SessionSettingItem,
  SessionSettingsActions,
  SessionSettingsFrameRenderer,
  SessionSettingsRenderers,
} from './types';

export interface SessionSettingsHostProps {
  items: SessionSettingItem[];
  actions: SessionSettingsActions;
  renderers: SessionSettingsRenderers;
  renderFrame?: SessionSettingsFrameRenderer;
}

export function SessionSettingsHost({
  items,
  actions,
  renderers,
  renderFrame,
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
          </Fragment>
        );
      }

      const renderFallback = () =>
        fallbackRenderer({ item, actions, renderFallback: () => null });

      return (
        <Fragment key={item.key}>
          {renderer({ item, actions, renderFallback })}
        </Fragment>
      );
    });
  }, [actions, items, renderers]);

  if (renderFrame) {
    return <>{renderFrame({ items, children: <>{content}</> })}</>;
  }

  return <>{content}</>;
}
