import type { SessionListOptionTone } from '@crystal-lattice/frontend-sdk';

import type { useTheme } from '../theme';

export function resolveSemanticToneColor(
  theme: ReturnType<typeof useTheme>,
  tone: SessionListOptionTone | undefined,
): string {
  switch (tone) {
    case 'highlight':
      return theme.highlight;
    case 'warning':
      return theme.warning;
    case 'success':
      return theme.success;
    case 'danger':
      return theme.danger;
    case 'muted':
      return theme.textMuted;
    case 'primary':
    default:
      return theme.primary;
  }
}
