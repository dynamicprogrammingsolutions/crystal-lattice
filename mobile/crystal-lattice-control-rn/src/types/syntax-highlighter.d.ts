declare module 'react-native-syntax-highlighter' {
  import type { ComponentType } from 'react';

  const SyntaxHighlighter: ComponentType<any>;
  export default SyntaxHighlighter;
}

declare module 'react-syntax-highlighter/styles/hljs' {
  export const atomOneDark: any;
  const styles: any;
  export default styles;
}
