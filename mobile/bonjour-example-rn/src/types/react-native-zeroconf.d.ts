declare module 'react-native-zeroconf' {
  export default class Zeroconf {
    scan(type?: string, protocol?: string, domain?: string): void;
    stop(): void;
    on(event: string, callback: (data: any) => void): void;
    removeAllListeners(): void;
  }
}
