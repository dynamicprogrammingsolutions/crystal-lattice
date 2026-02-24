import { NativeModules, Platform } from 'react-native';

export type PickedMacAttachment = {
  filename: string;
  mime_type: string;
  data_base64: string;
};

type MacAttachmentPickerNative = {
  pick: (params: { allowedExtensions?: string[]; maxBytes?: number }) => Promise<PickedMacAttachment | null>;
};

const NativeMacAttachmentPicker = (NativeModules as any)
  ?.MacAttachmentPicker as MacAttachmentPickerNative | undefined;

export async function pickMacAttachment(params: {
  allowedExtensions?: string[];
  maxBytes?: number;
}): Promise<PickedMacAttachment | null> {
  if (Platform.OS !== 'macos') {
    throw new Error('MacAttachmentPicker is only available on macOS.');
  }

  if (!NativeMacAttachmentPicker?.pick) {
    throw new Error('MacAttachmentPicker native module is not available.');
  }

  return NativeMacAttachmentPicker.pick({
    allowedExtensions: params.allowedExtensions,
    maxBytes: params.maxBytes,
  });
}
