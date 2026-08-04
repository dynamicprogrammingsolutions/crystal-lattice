import {
  countActiveSessionListFilters,
  createSessionListFilterValues,
  evaluateSessionListFilters,
  validateSessionListFilterValue,
  withFrontendFallbackSessionSearch,
  type SessionListFilterElement,
  type SessionListFilterSchema,
  type SessionListFilterValues,
  type SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { useCallback, useEffect, useMemo, useState } from 'react';

export interface UseSessionListFiltersOptions {
  connectionId: string | null;
  schema: SessionListFilterSchema;
}

export interface UseSessionListFiltersResult {
  schema: SessionListFilterSchema;
  values: SessionListFilterValues;
  mainSearch: SessionListFilterElement;
  searchText: string;
  nonMainFilters: readonly SessionListFilterElement[];
  activeNonMainFilterCount: number;
  setFilterValue: (filterId: string, value: unknown) => void;
  setSearchText: (value: string) => void;
  reset: () => void;
  showAll: () => void;
  filterSessions: (sessions: SessionSummary[]) => SessionSummary[];
}

interface ScopedFilterState {
  scopeIdentity: string;
  values: SessionListFilterValues;
}

export function useSessionListFilters(
  options: UseSessionListFiltersOptions,
): UseSessionListFiltersResult {
  const schema = useMemo(
    () => withFrontendFallbackSessionSearch(options.schema),
    [options.schema],
  );
  const scopeIdentity = `${options.connectionId ?? 'default'}:${schema.identity}`;
  const defaults = useMemo(
    () => createSessionListFilterValues(schema),
    [schema],
  );
  const [stored, setStored] = useState<ScopedFilterState>(() => ({
    scopeIdentity,
    values: defaults,
  }));
  const values =
    stored.scopeIdentity === scopeIdentity ? stored.values : defaults;

  useEffect(() => {
    if (stored.scopeIdentity !== scopeIdentity) {
      setStored({ scopeIdentity, values: defaults });
    }
  }, [defaults, scopeIdentity, stored.scopeIdentity]);

  const setFilterValue = useCallback(
    (filterId: string, value: unknown) => {
      const filter = schema.filters.find((item) => item.id === filterId);
      if (!filter) {
        throw new Error(`Unknown session-list filter ${JSON.stringify(filterId)}`);
      }
      const valueError = validateSessionListFilterValue(filter, value);
      if (valueError) {
        throw new Error(
          `Value for session-list filter ${JSON.stringify(filterId)} ${valueError}.`,
        );
      }
      setStored((current) => {
        const base =
          current.scopeIdentity === scopeIdentity ? current.values : defaults;
        return {
          scopeIdentity,
          values: {
            ...base,
            [filterId]: value,
          },
        };
      });
    },
    [defaults, schema.filters, scopeIdentity],
  );

  const mainSearch = schema.mainSearch!;
  const setSearchText = useCallback(
    (value: string) => setFilterValue(mainSearch.id, value),
    [mainSearch.id, setFilterValue],
  );
  const reset = useCallback(() => {
    setStored({
      scopeIdentity,
      values: createSessionListFilterValues(schema),
    });
  }, [schema, scopeIdentity]);
  const showAll = useCallback(() => {
    setStored({
      scopeIdentity,
      values: createSessionListFilterValues(schema, 'show_all'),
    });
  }, [schema, scopeIdentity]);
  const nonMainFilters = useMemo(
    () => schema.filters.filter((filter) => filter.id !== mainSearch.id),
    [mainSearch.id, schema.filters],
  );
  const activeNonMainFilterCount = useMemo(
    () =>
      countActiveSessionListFilters(schema, values, {
        excludeMainSearch: true,
      }),
    [schema, values],
  );
  const filterSessions = useCallback(
    (sessions: SessionSummary[]) =>
      evaluateSessionListFilters(sessions, schema, values).sessions,
    [schema, values],
  );
  const rawSearchText = values[mainSearch.id];

  return {
    schema,
    values,
    mainSearch,
    searchText: typeof rawSearchText === 'string' ? rawSearchText : '',
    nonMainFilters,
    activeNonMainFilterCount,
    setFilterValue,
    setSearchText,
    reset,
    showAll,
    filterSessions,
  };
}