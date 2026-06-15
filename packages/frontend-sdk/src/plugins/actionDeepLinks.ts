export interface ParsedActionDeepLink {
  pluginId?: string;
  actionId: string;
  inputs: Record<string, string>;
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

function decodeQueryPart(value: string): string | null {
  try {
    return decodeURIComponent(value.replace(/\+/g, ' '));
  } catch {
    return null;
  }
}

function parseQueryString(query: string): Record<string, string> | null {
  const inputs: Record<string, string> = {};
  if (!query) {
    return inputs;
  }

  for (const part of query.split('&')) {
    if (!part) continue;
    const equalsIndex = part.indexOf('=');
    const rawKey = equalsIndex === -1 ? part : part.slice(0, equalsIndex);
    const rawValue = equalsIndex === -1 ? '' : part.slice(equalsIndex + 1);
    const key = decodeQueryPart(rawKey);
    const value = decodeQueryPart(rawValue);
    if (!key || value === null) {
      return null;
    }
    inputs[key] = value;
  }

  return inputs;
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
  const query = queryIndex === -1 ? '' : withoutFragment.slice(queryIndex + 1);

  const segments = path
    .split('/')
    .filter(Boolean)
    .map(decodePathSegment);
  if (segments.some((segment) => segment === null)) {
    return null;
  }

  const decodedSegments = segments as string[];
  if (decodedSegments.length !== 1 && decodedSegments.length !== 2) {
    return null;
  }

  const inputs = parseQueryString(query);
  if (inputs === null) {
    return null;
  }
  inputs.redirect_url = rawUrl;

  if (decodedSegments.length === 1) {
    return {
      actionId: decodedSegments[0],
      inputs,
      redirectUrl: rawUrl,
    };
  }

  return {
    pluginId: decodedSegments[0],
    actionId: decodedSegments[1],
    inputs,
    redirectUrl: rawUrl,
  };
}