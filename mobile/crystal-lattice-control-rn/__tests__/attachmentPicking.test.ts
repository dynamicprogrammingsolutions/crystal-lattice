import RNFS from 'react-native-fs';
import { Platform } from 'react-native';
import {
  errorCodes,
  keepLocalCopy,
  pick,
} from '@react-native-documents/picker';
import {
  launchCamera,
  launchImageLibrary,
} from 'react-native-image-picker';

import { pickAssetAsDataUrl } from '../src/attachmentPicking';

const pickMock = pick as jest.MockedFunction<typeof pick>;
const keepLocalCopyMock = keepLocalCopy as jest.MockedFunction<typeof keepLocalCopy>;
const launchImageLibraryMock = launchImageLibrary as jest.MockedFunction<typeof launchImageLibrary>;
const launchCameraMock = launchCamera as jest.MockedFunction<typeof launchCamera>;
const readFileMock = RNFS.readFile as jest.MockedFunction<typeof RNFS.readFile>;

beforeEach(() => {
  jest.clearAllMocks();
});

test('image file picking uses the document picker path', async () => {
  pickMock.mockResolvedValue([
    {
      name: 'scan.png',
      uri: 'content://scan',
      type: 'image/png',
      size: 123,
    } as any,
  ]);
  keepLocalCopyMock.mockResolvedValue([
    {
      status: 'success',
      localUri: 'file:///tmp/scan.png',
    } as any,
  ]);
  readFileMock.mockResolvedValue('QUJD');

  const result = await pickAssetAsDataUrl({
    attachmentType: 'image',
    supportedFileTypes: ['png'],
    source: 'files',
  });

  expect(pickMock).toHaveBeenCalledWith({
    type: ['public.image'],
    allowMultiSelection: false,
    mode: Platform.OS === 'android' ? 'open' : 'import',
  });
  expect(keepLocalCopyMock).toHaveBeenCalledWith({
    files: [{ uri: 'content://scan', fileName: 'scan.png' }],
    destination: 'cachesDirectory',
  });
  expect(launchImageLibraryMock).not.toHaveBeenCalled();
  expect(launchCameraMock).not.toHaveBeenCalled();
  expect(result).toEqual({
    filename: 'scan.png',
    mimeType: 'image/png',
    dataUrl: 'data:image/png;base64,QUJD',
    sizeBytes: 123,
  });
});

test('image library picking stays on the photo picker path', async () => {
  launchImageLibraryMock.mockResolvedValue({
    assets: [
      {
        base64: 'Rk9P',
        fileName: 'photo.png',
        type: 'image/png',
        fileSize: 456,
      },
    ],
  } as any);

  const result = await pickAssetAsDataUrl({
    attachmentType: 'image',
    supportedFileTypes: ['png'],
    source: 'library',
  });

  expect(launchImageLibraryMock).toHaveBeenCalledWith({
    mediaType: 'photo',
    selectionLimit: 1,
    includeBase64: true,
    saveToPhotos: false,
  });
  expect(pickMock).not.toHaveBeenCalled();
  expect(result).toEqual({
    filename: 'photo.png',
    mimeType: 'image/png',
    dataUrl: 'data:image/png;base64,Rk9P',
    sizeBytes: 456,
  });
});

test('document picker in-progress errors become actionable messages', async () => {
  pickMock.mockRejectedValue(
    Object.assign(new Error('busy'), { code: errorCodes.IN_PROGRESS }),
  );

  await expect(
    pickAssetAsDataUrl({
      attachmentType: 'pdf',
      supportedFileTypes: ['pdf'],
    }),
  ).rejects.toThrow(
    'Another file picker is still active. If no picker is visible, reset the picker and try again.',
  );
});