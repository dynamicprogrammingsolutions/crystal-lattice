import {
  errorCodes,
  isErrorWithCode,
  pickDirectory,
} from "@react-native-documents/picker";
import type { ActionUiElement } from "@crystal-lattice/frontend-sdk";

import { registerEmbeddedWorkspaceDirectoryGrant } from "./embeddedRuntime/embeddedPythonRuntime";

export async function acquireActionClientValues(
  element: ActionUiElement,
): Promise<Record<string, unknown> | null> {
  const clientInput = element.client_input;
  if (!clientInput) {
    return {};
  }
  if (
    clientInput.kind !== "directory" ||
    typeof clientInput.input_name !== "string" ||
    !clientInput.input_name
  ) {
    throw new Error(`Unsupported client input: ${String(clientInput.kind)}`);
  }

  try {
    const picked = await pickDirectory({
      requestLongTermAccess: clientInput.persistent !== false,
    });
    if (!picked || typeof picked.uri !== "string" || !picked.uri) {
      throw new Error("The directory picker did not return a folder.");
    }
    const bookmark =
      (picked as any).bookmarkStatus === "success" &&
      typeof (picked as any).bookmark === "string"
        ? (picked as any).bookmark
        : undefined;
    if (clientInput.persistent !== false && !bookmark) {
      const detail =
        typeof (picked as any).bookmarkError === "string"
          ? `: ${(picked as any).bookmarkError}`
          : "";
      throw new Error(`The selected folder could not be retained${detail}`);
    }
    const grant = await registerEmbeddedWorkspaceDirectoryGrant({
      uri: picked.uri,
      bookmark,
    });
    return {
      [clientInput.input_name]: grant.grantId,
    };
  } catch (error: any) {
    if (
      isErrorWithCode(error) &&
      error.code === errorCodes.OPERATION_CANCELED
    ) {
      return null;
    }
    throw error;
  }
}