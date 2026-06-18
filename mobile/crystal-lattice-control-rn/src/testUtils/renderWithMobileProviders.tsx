import React from 'react';
import { render, type RenderOptions } from '@testing-library/react-native';

import { ThemeProvider, lightTheme } from '../theme';

export function renderWithMobileProviders(
  ui: React.ReactElement,
  options?: RenderOptions,
) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>, options);
}
