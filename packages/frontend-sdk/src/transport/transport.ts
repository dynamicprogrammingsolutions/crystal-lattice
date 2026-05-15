export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface PathPrefixTimeoutRule {
  pathPrefix: string;
  timeoutMs: number;
  method?: HttpMethod | HttpMethod[];
}

export interface TransportTimeoutRule {
  timeoutMs: number;
  method?: HttpMethod | HttpMethod[];
  pathPrefix?: string;
  pathRegex?: RegExp;
}

export interface Transport {
  request<T = any>(req: {
    method: HttpMethod;
    path: string;
    headers?: Record<string, string>;
    body?: any;
    timeoutMs?: number;
  }): Promise<{ status: number; data: T }>;
}

function matchesMethod(ruleMethod: HttpMethod | HttpMethod[] | undefined, method: HttpMethod): boolean {
  if (!ruleMethod) {
    return true;
  }
  if (Array.isArray(ruleMethod)) {
    return ruleMethod.includes(method);
  }
  return ruleMethod === method;
}

function getPathMatchScore(rule: TransportTimeoutRule, path: string): number {
  if (rule.pathPrefix && !path.startsWith(rule.pathPrefix)) {
    return -1;
  }
  if (rule.pathRegex && !rule.pathRegex.test(path)) {
    return -1;
  }

  const prefixScore = rule.pathPrefix ? rule.pathPrefix.length : 0;
  const regexScore = rule.pathRegex ? rule.pathRegex.source.length : 0;
  return Math.max(prefixScore, regexScore);
}

export function resolveTransportTimeoutMs(options: {
  method: HttpMethod;
  path: string;
  timeoutMs?: number;
  defaultRequestTimeoutMs?: number;
  timeoutRules?: TransportTimeoutRule[];
  timeoutMsByPathPrefix?: PathPrefixTimeoutRule[];
}): number | undefined {
  if (typeof options.timeoutMs === 'number') {
    return options.timeoutMs;
  }

  const rules: TransportTimeoutRule[] = [
    ...(options.timeoutRules ?? []),
    ...((options.timeoutMsByPathPrefix ?? []) as TransportTimeoutRule[]),
  ];

  let best: { timeoutMs: number; methodSpecificity: number; pathSpecificity: number } | null = null;
  for (const rule of rules) {
    if (!rule || typeof rule.timeoutMs !== 'number') {
      continue;
    }
    if (!matchesMethod(rule.method, options.method)) {
      continue;
    }

    const pathSpecificity = getPathMatchScore(rule, options.path);
    if (pathSpecificity < 0) {
      continue;
    }

    const methodSpecificity = rule.method ? 1 : 0;
    if (
      !best ||
      methodSpecificity > best.methodSpecificity ||
      (methodSpecificity === best.methodSpecificity && pathSpecificity > best.pathSpecificity)
    ) {
      best = {
        timeoutMs: rule.timeoutMs,
        methodSpecificity,
        pathSpecificity,
      };
    }
  }

  if (best) {
    return best.timeoutMs;
  }
  return options.defaultRequestTimeoutMs;
}
