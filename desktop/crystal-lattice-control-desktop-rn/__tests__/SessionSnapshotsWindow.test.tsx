/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import { SessionSnapshotsWindow } from '../src/windows/SessionSnapshotsWindow';
import {
  clearActiveSessionSnapshotsWindow,
  setActiveSessionSnapshotsWindow,
} from '../src/windows/sessionSnapshotsCoordinator';

type SnapshotSummary = {
  snapshot_id: string;
  session_id?: string;
  created_at: string;
  reason?: string | null;
};

function makeBackend(opts: {
  list?: SnapshotSummary[];
  listThrows?: Error;
  create?: SnapshotSummary;
  createThrows?: Error;
} = {}) {
  const list = opts.list ?? [];
  const created = opts.create ?? {
    snapshot_id: 'snap-new',
    session_id: 's1',
    created_at: '2026-06-17T12:00:00Z',
    reason: 'manual',
  };
  const calls = {
    listSessionSnapshots: 0,
    createSessionSnapshot: 0,
  };
  const backend: any = {
    listSessionSnapshots: async () => {
      calls.listSessionSnapshots += 1;
      if (opts.listThrows) {
        throw opts.listThrows;
      }
      return list;
    },
    createSessionSnapshot: async () => {
      calls.createSessionSnapshot += 1;
      if (opts.createThrows) {
        throw opts.createThrows;
      }
      return created;
    },
  };
  return { backend, calls };
}

let renderer: ReactTestRenderer.ReactTestRenderer | null = null;

function setActive(backend: any, sessionId = 's1') {
  ReactTestRenderer.act(() => {
    setActiveSessionSnapshotsWindow({
      state: {
        id: `session-snapshots:conn1:${sessionId}`,
        connectionId: 'conn1',
        connectionName: 'Connection 1',
        sessionId,
        backend,
      },
    });
  });
}

async function renderAndWait(element: React.ReactElement) {
  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(element);
    await Promise.resolve();
    await Promise.resolve();
  });
  return renderer!;
}

function findAllByText(
  root: ReactTestRenderer.ReactTestInstance,
  text: string,
): ReactTestRenderer.ReactTestInstance[] {
  const matches: ReactTestRenderer.ReactTestInstance[] = [];
  function visit(node: ReactTestRenderer.ReactTestInstance) {
    const children = node.children ?? [];
    for (const child of children) {
      if (typeof child === 'string' && child === text) {
        matches.push(node);
      } else if (typeof child === 'object' && child !== null && (child as any).type !== undefined) {
        visit(child as ReactTestRenderer.ReactTestInstance);
      }
    }
  }
  visit(root);
  return matches;
}

function findPressableByText(
  root: ReactTestRenderer.ReactTestInstance,
  text: string,
): ReactTestRenderer.ReactTestInstance {
  const all = root.findAll((node: any) => typeof node.props?.onPress === 'function');
  for (const node of all) {
    const texts = (node as ReactTestRenderer.ReactTestInstance).findAll(
      (n: any) => typeof n === 'object' && n !== null && n.children?.some?.((c: any) => typeof c === 'string' && c === text),
    );
    if (texts.length > 0) {
      return node as ReactTestRenderer.ReactTestInstance;
    }
  }
  throw new Error(`No pressable with text "${text}" found`);
}

afterEach(async () => {
  await ReactTestRenderer.act(async () => {
    if (renderer) {
      renderer.unmount();
      renderer = null;
    }
    clearActiveSessionSnapshotsWindow();
    await Promise.resolve();
  });
});

test('renders title, close, and create with loaded snapshot items', async () => {
  const { backend, calls } = makeBackend({
    list: [
      {
        snapshot_id: 'snap-1',
        created_at: '2026-06-17T12:00:00Z',
        reason: 'manual',
      },
      {
        snapshot_id: 'snap-2',
        created_at: '2026-06-17T13:00:00Z',
        reason: null,
      },
    ],
  });
  setActive(backend);

  const r = await renderAndWait(<SessionSnapshotsWindow />);
  const root = r.root;

  expect(findAllByText(root, 'Snapshots').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'Close').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'Create').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'manual').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'snapshot').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'snap-1').length).toBeGreaterThan(0);
  expect(findAllByText(root, 'snap-2').length).toBeGreaterThan(0);
  expect(calls.listSessionSnapshots).toBe(1);
  expect(calls.createSessionSnapshot).toBe(0);
});

test('renders empty state when no snapshots exist', async () => {
  const { backend } = makeBackend({ list: [] });
  setActive(backend);

  const r = await renderAndWait(<SessionSnapshotsWindow />);
  const root = r.root;

  expect(findAllByText(root, 'No snapshots yet.').length).toBeGreaterThan(0);
});

test('create calls backend.createSessionSnapshot then reloads the list', async () => {
  let listCalls = 0;
  let createCalls = 0;
  const backend: any = {
    listSessionSnapshots: async () => {
      listCalls += 1;
      return [];
    },
    createSessionSnapshot: async () => {
      createCalls += 1;
      return {
        snapshot_id: 'snap-new',
        session_id: 's1',
        created_at: '2026-06-17T12:00:00Z',
        reason: 'manual',
      };
    },
  };
  setActive(backend);

  const r = await renderAndWait(<SessionSnapshotsWindow />);
  const root = r.root;

  expect(listCalls).toBe(1);
  expect(createCalls).toBe(0);

  const createButtons = findAllByText(root, 'Create');
  expect(createButtons.length).toBeGreaterThan(0);

  const createPressable = findPressableByText(root, 'Create');

  await ReactTestRenderer.act(async () => {
    createPressable.props.onPress();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });

  expect(createCalls).toBe(1);
  expect(listCalls).toBe(2);
});

test('close clears the active snapshots window', async () => {
  const { backend } = makeBackend({ list: [] });
  setActive(backend);

  const r = await renderAndWait(<SessionSnapshotsWindow />);
  const root = r.root;

  const closeButtons = findAllByText(root, 'Close');
  expect(closeButtons.length).toBeGreaterThan(0);

  const closePressable = findPressableByText(root, 'Close');

  await ReactTestRenderer.act(async () => {
    closePressable.props.onPress();
    await Promise.resolve();
  });

  await ReactTestRenderer.act(async () => {
    r.update(<SessionSnapshotsWindow />);
    await Promise.resolve();
  });

  expect(findAllByText(r.root, 'Snapshots').length).toBe(0);
});

test('renders error message when listing fails', async () => {
  const { backend } = makeBackend({ listThrows: new Error('boom') });
  setActive(backend);

  const r = await renderAndWait(<SessionSnapshotsWindow />);
  const root = r.root;

  expect(findAllByText(root, 'boom').length).toBeGreaterThan(0);
});