import React from 'react';
import type { CodeBlockRendererId } from '@crystal-lattice/frontend-rn-components';

import SelectableCodeBlock from './SelectableCodeBlock';
import SyntaxHighlightedCodeBlock from './SyntaxHighlightedCodeBlock';

export interface ConfiguredCodeBlockProps {
  renderer: CodeBlockRendererId;
  language?: string;
  code: string;
}

const ConfiguredCodeBlock: React.FC<ConfiguredCodeBlockProps> = ({
  renderer,
  language,
  code,
}) => {
  if (renderer === 'syntax-highlighter') {
    return (
      <SyntaxHighlightedCodeBlock
        language={language}
        code={code}
      />
    );
  }

  return (
    <SelectableCodeBlock
      language={language}
      code={code}
      testID="markdown-code-renderer-selectable-native"
    />
  );
};

export default React.memo(ConfiguredCodeBlock);