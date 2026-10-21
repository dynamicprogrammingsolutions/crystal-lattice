import { describe, expect, it } from 'vitest';
import {
  deriveBridgeHttpBaseUrl,
  deriveBridgeWebSocketUrl,
  normalizeBridgeAddress,
} from '../index';

describe('bridge address input', () => {
  it.each([
    ['bridge.example.com', 'https://bridge.example.com', 'wss://bridge.example.com/ws/websocket'],
    [' bridge.example.com:4443 ', 'https://bridge.example.com:4443', 'wss://bridge.example.com:4443/ws/websocket'],
    ['bridge.example.com/prefix', 'https://bridge.example.com/prefix', 'wss://bridge.example.com/prefix/ws/websocket'],
    ['https://bridge.example.com', 'https://bridge.example.com', 'wss://bridge.example.com/ws/websocket'],
    ['http://localhost:4000', 'http://localhost:4000', 'ws://localhost:4000/ws/websocket'],
    ['ws://localhost:4000/ws/websocket', 'http://localhost:4000', 'ws://localhost:4000/ws/websocket'],
    ['wss://bridge.example.com/prefix/ws/websocket', 'https://bridge.example.com/prefix', 'wss://bridge.example.com/prefix/ws/websocket'],
  ])('resolves %s consistently for HTTP and legacy diagnostics', (input, http, websocket) => {
    expect(deriveBridgeHttpBaseUrl(input)).toBe(http);
    expect(deriveBridgeWebSocketUrl(input)).toBe(websocket);
  });

  it('keeps configured legacy endpoint and query intact', () => {
    const address = 'wss://bridge.example.com/custom-socket?type=app';
    expect(normalizeBridgeAddress(` ${address} `)).toBe(address);
    expect(deriveBridgeWebSocketUrl(address)).toBe(address);
  });

  it.each(['', '  ', 'ftp://bridge.example.com', 'https://', 'bridge example.com'])(
    'rejects invalid address %s',
    (address) => expect(() => normalizeBridgeAddress(address)).toThrow(),
  );
});