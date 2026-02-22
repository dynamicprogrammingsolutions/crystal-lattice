import { NativeModules, findNodeHandle } from 'react-native';

export type ScrollViewMetrics = {
  offsetY: number;
  viewportHeight: number;
  contentHeight: number;
};

type NativeMacScrollViewMetrics = {
  getMetrics: (reactTag: number) => Promise<ScrollViewMetrics>;
};

const NativeMacScrollViewMetricsModule = NativeModules.MacScrollViewMetrics as
  | NativeMacScrollViewMetrics
  | undefined;

export async function getMacScrollViewMetrics(target: unknown): Promise<ScrollViewMetrics | null> {
  if (!NativeMacScrollViewMetricsModule) {
    return null;
  }

  const anyTarget = target as any;
  const scrollableNode =
    typeof anyTarget?.getScrollableNode === 'function' ? anyTarget.getScrollableNode() : null;
  const resolvedTarget =
    typeof anyTarget?.getNativeScrollRef === 'function' ? anyTarget.getNativeScrollRef() : anyTarget;

  const tag =
    typeof scrollableNode === 'number'
      ? scrollableNode
      : findNodeHandle(scrollableNode ?? resolvedTarget);
  if (!tag) {
    return null;
  }
  try {
    return await NativeMacScrollViewMetricsModule.getMetrics(tag);
  } catch {
    return null;
  }
}
