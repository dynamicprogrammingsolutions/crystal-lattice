import { useEffect, useRef } from 'react';

export function useHydrateControllerFromCache<TController, TCache>(options: {
  controller: TController | null;
  cache: TCache | null | undefined;
  hydrate: (controller: TController, cache: TCache) => void;
}): void {
  const { controller, cache, hydrate } = options;
  const hasHydratedRef = useRef(false);

  useEffect(() => {
    hasHydratedRef.current = false;
  }, [controller]);

  useEffect(() => {
    if (!controller) return;
    if (hasHydratedRef.current) return;
    if (cache == null) return;
    hydrate(controller, cache);
    hasHydratedRef.current = true;
  }, [controller, cache, hydrate]);
}
