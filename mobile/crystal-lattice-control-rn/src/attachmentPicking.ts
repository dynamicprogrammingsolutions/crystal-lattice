import DocumentPicker from 'react-native-document-picker';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import RNFS from 'react-native-fs';

export type PickedAssetDataUrl = {
  filename: string;
  mimeType: string;
  dataUrl: string;
  sizeBytes?: number;
};

function normalizeFilePath(uri: string): string {
  return uri.startsWith('file://') ? uri.slice('file://'.length) : uri;
}

function extensionFromFilename(filename: string): string {
  const idx = filename.lastIndexOf('.');
  if (idx < 0) return '';
  return filename.slice(idx + 1).trim().toLowerCase();
}

function inferMimeTypeFromExtension(ext: string): string {
  switch (ext) {
    case 'png':
      return 'image/png';
    case 'jpg':
    case 'jpeg':
      return 'image/jpeg';
    case 'gif':
      return 'image/gif';
    case 'webp':
      return 'image/webp';
    case 'pdf':
      return 'application/pdf';
    default:
      return 'application/octet-stream';
  }
}

function pickTypeForExtensions(exts: string[]): string[] {
  const normalized = exts.map((ext) => ext.trim().toLowerCase()).filter(Boolean);
  const hasPdf = normalized.includes('pdf');
  const imageExts = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp']);
  const hasImage = normalized.some((ext) => imageExts.has(ext));

  if (hasImage && !hasPdf) {
    return [DocumentPicker.types.images];
  }
  if (hasPdf && !hasImage) {
    return [DocumentPicker.types.pdf];
  }
  if (hasPdf && hasImage) {
    return [DocumentPicker.types.images, DocumentPicker.types.pdf];
  }
  return [DocumentPicker.types.allFiles];
}

async function pickDocumentAsDataUrl(options: {
  supportedFileTypes: string[];
}): Promise<PickedAssetDataUrl | null> {
  try {
    const result = await DocumentPicker.pickSingle({
      type: pickTypeForExtensions(options.supportedFileTypes),
      copyTo: 'cachesDirectory',
    });

    const filenameRaw =
      typeof (result as any).name === 'string' && (result as any).name.trim()
        ? (result as any).name.trim()
        : 'attachment';
    const filename = filenameRaw;
    const ext = extensionFromFilename(filename);

    if (options.supportedFileTypes.length > 0 && ext) {
      const allowed = new Set(
        options.supportedFileTypes.map((t) => t.trim().toLowerCase()).filter(Boolean),
      );
      if (!allowed.has(ext)) {
        throw new Error(`Unsupported file type: .${ext}`);
      }
    }

    const fileUri =
      typeof (result as any).fileCopyUri === 'string' && (result as any).fileCopyUri
        ? (result as any).fileCopyUri
        : typeof (result as any).uri === 'string'
          ? (result as any).uri
          : null;
    if (!fileUri) {
      throw new Error('No file URI from document picker');
    }

    if (fileUri.startsWith('content://') && !(result as any).fileCopyUri) {
      throw new Error(
        'Picked asset has a content:// URI without a file copy; cannot read as base64.',
      );
    }

    const mimeTypeRaw = typeof (result as any).type === 'string' ? (result as any).type : '';
    const mimeType = mimeTypeRaw || inferMimeTypeFromExtension(ext);
    const sizeBytes = typeof (result as any).size === 'number' ? (result as any).size : undefined;
    const base64 = await RNFS.readFile(normalizeFilePath(fileUri), 'base64');
    const dataUrl = `data:${mimeType};base64,${base64}`;
    return { filename, mimeType, dataUrl, sizeBytes };
  } catch (err: any) {
    if (DocumentPicker.isCancel(err)) {
      return null;
    }
    throw err;
  }
}

async function pickImageAsDataUrl(options: {
  supportedFileTypes: string[];
  source: 'library' | 'camera';
}): Promise<PickedAssetDataUrl | null> {
  const pickerFn = options.source === 'camera' ? launchCamera : launchImageLibrary;
  const result = await pickerFn({
    mediaType: 'photo',
    selectionLimit: 1,
    includeBase64: true,
    saveToPhotos: false,
  });

  if (result.didCancel) {
    return null;
  }
  if (result.errorCode) {
    const message = result.errorMessage || result.errorCode;
    throw new Error(message);
  }

  const asset = Array.isArray(result.assets) && result.assets.length > 0 ? result.assets[0] : null;
  if (!asset) {
    throw new Error('No image asset returned from picker');
  }

  const base64 = typeof asset.base64 === 'string' ? asset.base64 : '';
  if (!base64) {
    throw new Error('Image picker did not return base64 data');
  }

  const filename =
    typeof asset.fileName === 'string' && asset.fileName.trim()
      ? asset.fileName.trim()
      : 'image';
  const ext = extensionFromFilename(filename);
  if (options.supportedFileTypes.length > 0 && ext) {
    const allowed = new Set(
      options.supportedFileTypes.map((t) => t.trim().toLowerCase()).filter(Boolean),
    );
    if (!allowed.has(ext)) {
      throw new Error(`Unsupported file type: .${ext}`);
    }
  }

  const mimeType =
    typeof asset.type === 'string' && asset.type
      ? asset.type
      : inferMimeTypeFromExtension(ext);
  const sizeBytes = typeof asset.fileSize === 'number' ? asset.fileSize : undefined;
  const dataUrl = `data:${mimeType};base64,${base64}`;
  return { filename, mimeType, dataUrl, sizeBytes };
}

export async function pickAssetAsDataUrl(options: {
  attachmentType?: string;
  supportedFileTypes?: string[];
  imageSource?: 'library' | 'camera';
}): Promise<PickedAssetDataUrl | null> {
  const supportedFileTypes = Array.isArray(options.supportedFileTypes)
    ? options.supportedFileTypes
    : [];
  const attachmentType =
    typeof options.attachmentType === 'string' ? options.attachmentType.trim().toLowerCase() : '';

  if (attachmentType === 'image') {
    return pickImageAsDataUrl({
      supportedFileTypes,
      source: options.imageSource === 'camera' ? 'camera' : 'library',
    });
  }
  if (attachmentType === 'pdf') {
    return pickDocumentAsDataUrl({ supportedFileTypes });
  }

  const normalized = supportedFileTypes.map((t) => t.trim().toLowerCase()).filter(Boolean);
  const imageExts = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp']);
  const hasImage = normalized.some((ext) => imageExts.has(ext));
  const hasPdf = normalized.includes('pdf');

  if (hasImage && !hasPdf) {
    return pickImageAsDataUrl({
      supportedFileTypes,
      source: options.imageSource === 'camera' ? 'camera' : 'library',
    });
  }
  return pickDocumentAsDataUrl({ supportedFileTypes });
}
