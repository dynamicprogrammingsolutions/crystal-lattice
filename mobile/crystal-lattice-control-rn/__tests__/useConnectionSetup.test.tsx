import { act, renderHook } from "@testing-library/react-native";
import type {
  ConnectionRecord,
  Transport,
} from "@crystal-lattice/frontend-sdk";
import { useConnectionSetup } from "../src/connections/useConnectionSetup";

const record: ConnectionRecord = {
  id: "new",
  kind: "manual",
  name: "New server",
  host: "127.0.0.1",
  port: 8080,
  lastUsedAt: 1,
};

function transport() {
  return {
    request: jest.fn(),
    disconnect: jest.fn(),
  } as unknown as Transport & { disconnect: jest.Mock };
}

test("retains the active transport until a candidate is accepted", () => {
  const previous = transport();
  const next = transport();
  const onConnected = jest.fn();
  const { result } = renderHook(() =>
    useConnectionSetup({ transport: previous, onConnected })
  );
  act(() => result.current.start());
  const ticket = result.current.ticket();
  act(() => result.current.track(ticket, next));
  expect(previous.disconnect).not.toHaveBeenCalled();
  expect(onConnected).not.toHaveBeenCalled();
  act(() => result.current.complete(ticket, next, record));
  expect(onConnected).toHaveBeenCalledWith(next, record, undefined);
  expect(previous.disconnect).toHaveBeenCalledTimes(1);
  expect(next.disconnect).not.toHaveBeenCalled();
});

test.each(["cancel", "fail"] as const)(
  "%s closes a candidate and retains the active transport",
  (operation) => {
    const previous = transport();
    const next = transport();
    const onConnected = jest.fn();
    const { result } = renderHook(() =>
      useConnectionSetup({ transport: previous, onConnected })
    );
    const ticket = result.current.ticket();
    act(() => result.current.track(ticket, next));
    act(() => {
      if (operation === "cancel") result.current.cancel();
      else result.current.fail(ticket);
    });
    expect(previous.disconnect).not.toHaveBeenCalled();
    expect(next.disconnect).toHaveBeenCalledTimes(1);
    expect(onConnected).not.toHaveBeenCalled();
  }
);

test("rejects a late result after cancellation and a newer setup", () => {
  const previous = transport();
  const next = transport();
  const onConnected = jest.fn();
  const { result } = renderHook(() =>
    useConnectionSetup({ transport: previous, onConnected })
  );
  const ticket = result.current.ticket();
  act(() => result.current.track(ticket, next));
  act(() => result.current.cancel());
  act(() => result.current.start());
  act(() => expect(result.current.complete(ticket, next, record)).toBe(false));
  expect(previous.disconnect).not.toHaveBeenCalled();
  expect(onConnected).not.toHaveBeenCalled();
});
