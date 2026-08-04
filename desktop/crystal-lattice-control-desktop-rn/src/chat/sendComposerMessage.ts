import type { ChatController } from '@crystal-lattice/frontend-sdk';

type ComposerMessage = Parameters<ChatController['sendMessage']>[0]['message'];

export async function sendComposerMessageAtomically(
  chatController: Pick<ChatController, 'clearRequestState' | 'sendMessage'>,
  message: ComposerMessage,
): Promise<void> {
  chatController.clearRequestState();
  await chatController.sendMessage({ message });
}
