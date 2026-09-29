import { Platform } from 'react-native';
import {
  resolveMarkdownRendererPreferences,
  type MarkdownDisplayPreferences,
  type MarkdownRendererCapabilities,
  type ResolvedMarkdownRendererPreferences,
} from '@crystal-lattice/frontend-rn-components';

export function getMobileMarkdownRendererCapabilities(
  platform: string,
): MarkdownRendererCapabilities {
  return {
    enrichedMarkdown: platform === 'ios' || platform === 'android',
    selectableNativeCode: platform === 'ios',
  };
}

export const MOBILE_MARKDOWN_RENDERER_CAPABILITIES: Readonly<MarkdownRendererCapabilities> =
  getMobileMarkdownRendererCapabilities(Platform.OS);

export function resolveMobileMarkdownRendererPreferences(
  preferences: MarkdownDisplayPreferences,
): ResolvedMarkdownRendererPreferences {
  return resolveMarkdownRendererPreferences(
    preferences,
    MOBILE_MARKDOWN_RENDERER_CAPABILITIES,
  );
}