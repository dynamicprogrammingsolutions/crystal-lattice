import { describe, expect, it } from 'vitest';

import { evaluateCondition } from './uiSchema';

describe('evaluateCondition', () => {
  it('returns true for missing or falsy condition', () => {
    const ctx = { role: 'assistant' };
    expect(evaluateCondition(null, ctx)).toBe(true);
    expect(evaluateCondition(undefined, ctx)).toBe(true);
    expect(evaluateCondition({}, ctx)).toBe(true);
  });

  it('evalutes eq leaf', () => {
    const ctx = { role: 'assistant', metadata: { x: 1 } };
    expect(evaluateCondition({ path: 'role', eq: 'assistant' }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'role', eq: 'user' }, ctx)).toBe(false);
    expect(evaluateCondition({ path: 'metadata.x', eq: 1 }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'missing', eq: 'x' }, ctx)).toBe(false);
  });

  it('evaluates exists leaf', () => {
    const ctx = { role: 'assistant', empty: '' };
    expect(evaluateCondition({ path: 'role', exists: true }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'role', exists: false }, ctx)).toBe(false);
    expect(evaluateCondition({ path: 'missing', exists: true }, ctx)).toBe(false);
    expect(evaluateCondition({ path: 'missing', exists: false }, ctx)).toBe(true);
  });

  it('evaluates empty leaf', () => {
    const ctx = { a: null, b: '', c: [], d: {}, e: 'x', f: [1] };
    expect(evaluateCondition({ path: 'a', empty: true }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'b', empty: true }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'c', empty: true }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'd', empty: true }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'e', empty: true }, ctx)).toBe(false);
    expect(evaluateCondition({ path: 'f', empty: true }, ctx)).toBe(false);
    expect(evaluateCondition({ path: 'e', empty: false }, ctx)).toBe(true);
    expect(evaluateCondition({ path: 'missing', empty: true }, ctx)).toBe(true);
  });

  it('evaluates all composition', () => {
    const ctx = { role: 'assistant', metadata: { tool_calls: null } };
    const cond = {
      all: [
        { path: 'role', eq: 'assistant' },
        { path: 'metadata.tool_calls', empty: true },
      ],
    };
    expect(evaluateCondition(cond, ctx)).toBe(true);
    const ctx2 = { ...ctx, metadata: { tool_calls: [{ id: '1' }] } };
    expect(evaluateCondition(cond, ctx2)).toBe(false);
  });

  it('evaluates any composition', () => {
    const cond = { any: [{ path: 'role', eq: 'assistant' }, { path: 'role', eq: 'user' }] };
    expect(evaluateCondition(cond, { role: 'user' })).toBe(true);
    expect(evaluateCondition(cond, { role: 'assistant' })).toBe(true);
    expect(evaluateCondition(cond, { role: 'tool' })).toBe(false);
  });

  it('evaluates not composition', () => {
    const ctx = { role: 'assistant' };
    expect(evaluateCondition({ not: { path: 'role', eq: 'user' } }, ctx)).toBe(true);
    expect(evaluateCondition({ not: { path: 'role', eq: 'assistant' } }, ctx)).toBe(false);
  });
});
