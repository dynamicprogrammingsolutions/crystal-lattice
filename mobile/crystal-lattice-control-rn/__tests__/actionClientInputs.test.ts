import {
  errorCodes,
  pickDirectory,
} from '@react-native-documents/picker';

import { acquireActionClientValues } from '../src/actionClientInputs';
import { registerEmbeddedWorkspaceDirectoryGrant } from '../src/embeddedRuntime/embeddedPythonRuntime';

jest.mock('../src/embeddedRuntime/embeddedPythonRuntime', () => ({
  registerEmbeddedWorkspaceDirectoryGrant: jest.fn(),
}));

const pickDirectoryMock = pickDirectory as jest.MockedFunction<typeof pickDirectory>;
const registerGrantMock =
  registerEmbeddedWorkspaceDirectoryGrant as jest.MockedFunction<
    typeof registerEmbeddedWorkspaceDirectoryGrant
  >;

beforeEach(() => {
  jest.clearAllMocks();
});

test('directory client input returns only an opaque native grant id', async () => {
  pickDirectoryMock.mockResolvedValue({
    uri: 'file:///private/provider/project',
    bookmarkStatus: 'success',
    bookmark: 'Ym9va21hcms=',
  } as any);
  registerGrantMock.mockResolvedValue({
    grantId: 'grant-123',
    displayName: 'project',
  });

  const values = await acquireActionClientValues({
    ui_type: 'session_action',
    plugin: 'workspace',
    id: 'select_external_workspace',
    label: 'Choose folder',
    action_id: 'select_external_workspace',
    client_input: {
      kind: 'directory',
      input_name: 'workspace_grant_id',
      persistent: true,
    },
  });

  expect(registerGrantMock).toHaveBeenCalledWith({
    uri: 'file:///private/provider/project',
    bookmark: 'Ym9va21hcms=',
  });
  expect(values).toEqual({ workspace_grant_id: 'grant-123' });
  expect(JSON.stringify(values)).not.toContain('bookmark');
  expect(JSON.stringify(values)).not.toContain('/private/provider');
});

test('canceling directory selection returns null', async () => {
  pickDirectoryMock.mockRejectedValue(
    Object.assign(new Error('cancelled'), {
      code: errorCodes.OPERATION_CANCELED,
    }),
  );

  await expect(
    acquireActionClientValues({
      ui_type: 'session_action',
      plugin: 'workspace',
      id: 'select_external_workspace',
      label: 'Choose folder',
      action_id: 'select_external_workspace',
      client_input: {
        kind: 'directory',
        input_name: 'workspace_grant_id',
        persistent: true,
      },
    }),
  ).resolves.toBeNull();
  expect(registerGrantMock).not.toHaveBeenCalled();
});