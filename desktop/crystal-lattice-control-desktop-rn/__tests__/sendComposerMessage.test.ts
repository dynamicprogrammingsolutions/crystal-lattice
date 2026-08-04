import { sendComposerMessageAtomically } from '../src/chat/sendComposerMessage';

describe('sendComposerMessageAtomically', () => {
  it('uses the combined append-and-start API', async () => {
    const calls: string[] = [];
    const sendMessage = jest.fn(async () => {
      calls.push('sendMessage');
    });
    const controller = {
      clearRequestState: jest.fn(() => {
        calls.push('clearRequestState');
      }),
      sendMessage,
    };
    const message = {
      role: 'user' as const,
      content: 'hello',
      multipartContent: [],
    };

    await sendComposerMessageAtomically(controller, message);

    expect(calls).toEqual(['clearRequestState', 'sendMessage']);
    expect(sendMessage).toHaveBeenCalledWith({ message });
  });
});
