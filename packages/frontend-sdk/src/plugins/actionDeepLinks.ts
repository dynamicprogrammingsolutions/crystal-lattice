export interface ParsedActionDeepLink {
  connectionId: string;
  sessionId: string;
  pluginId?: string;
  callbackElementId: string;
  redirectUrl: string;
}

function decodePathSegment(segment: string): string | null {
  try {
    const decoded = decodeURIComponent(segment);
    return decoded ? decoded : null;
  } catch {
    return null;
  }
}

export function parseActionDeepLink(rawUrl: string): ParsedActionDeepLink | null {
  if (typeof rawUrl !== 'string' || !rawUrl) {
    return null;
  }

  const prefix = 'crystal-lattice://action';
  if (!rawUrl.startsWith(prefix)) {
    return null;
  }

  const route = rawUrl.slice(prefix.length);
  if (!route.startsWith('/')) {
    return null;
  }

  const withoutFragment = route.split('#', 1)[0];
  const queryIndex = withoutFragment.indexOf('?');
  const path = queryIndex === -1 ? withoutFragment : withoutFragment.slice(0, queryIndex);
  const segments = path
    .split('/')
    .filter(Boolean)
    .map(decodePathSegment);
  if (segments.some((segment) => segment === null)) {
    return null;
  }

  const decodedSegments = segments as string[];
  if (decodedSegments.length !== 3 && decodedSegments.length !== 4) {
    return null;
  }

  if (decodedSegments.length === 3) {
    return {
      connectionId: decodedSegments[0],
      sessionId: decodedSegments[1],
      callbackElementId: decodedSegments[2],
      redirectUrl: rawUrl,
    };
  }

  return {
    connectionId: decodedSegments[0],
    sessionId: decodedSegments[1],
    pluginId: decodedSegments[2],
    callbackElementId: decodedSegments[3],
    redirectUrl: rawUrl,
  };
}
