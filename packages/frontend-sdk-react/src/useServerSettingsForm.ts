import { useMemo } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import { buildConfigSchemaByKey, buildSessionSettingItems } from './sessionSettings';
import { useServerSettingsController } from './useServerSettingsController';

export function useServerSettingsForm(options: {
  backend: AgentBackend | null;
  cacheKey: string;
  enabled: boolean;
}) {
  const { controller, state } = useServerSettingsController(options);
  const schemaByKey = useMemo(() => buildConfigSchemaByKey([]), []);
  const items = useMemo(
    () =>
      buildSessionSettingItems({
        elements: state?.elements ?? [],
        overrides: state?.settings ?? {},
        baseConfig: state?.baseConfig ?? {},
        schemaByKey,
      }),
    [schemaByKey, state?.baseConfig, state?.elements, state?.settings],
  );
  const savingKeys = useMemo(
    () => new Set(state?.savingKeys ?? []),
    [state?.savingKeys],
  );
  return { controller, state, items, savingKeys };
}