import React from 'react';
import { View } from 'react-native';
import { useMarkdownDisplayPreferences } from '@crystal-lattice/frontend-rn-components';

import { resolveMobileMarkdownRendererPreferences } from '../markdownRendererPreferences';
import MarkdownMessageContent, {
  type MarkdownMessageContentProps,
} from './MarkdownMessageContent';
import SelectableMarkdownMessageContent from './SelectableMarkdownMessageContent';

export interface ConfiguredMarkdownMessageContentProps {
  text: MarkdownMessageContentProps['text'];
  variant?: MarkdownMessageContentProps['variant'];
  testID?: string;
}

const ConfiguredMarkdownMessageContent: React.FC<
  ConfiguredMarkdownMessageContentProps
> = ({
  text,
  variant = 'assistant',
  testID,
}) => {
  const { preferences } = useMarkdownDisplayPreferences();
  const resolved = resolveMobileMarkdownRendererPreferences(preferences);
  const rendererTestID = testID
    ? `${testID}-${resolved.markdownRenderer}`
    : undefined;

  return (
    <View testID={rendererTestID}>
      {resolved.markdownRenderer === 'react-native-enriched-markdown' ? (
        <SelectableMarkdownMessageContent
          text={text}
          variant={variant}
          codeBlockRenderer={resolved.codeBlockRenderer}
        />
      ) : (
        <MarkdownMessageContent
          text={text}
          variant={variant}
          codeBlockRenderer={resolved.codeBlockRenderer}
        />
      )}
    </View>
  );
};

export default React.memo(ConfiguredMarkdownMessageContent);