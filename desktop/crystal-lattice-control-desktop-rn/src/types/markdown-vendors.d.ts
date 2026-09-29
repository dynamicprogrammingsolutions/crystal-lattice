declare module 'react-syntax-highlighter/dist/cjs/styles/hljs';
declare module 'react-syntax-highlighter/dist/cjs/styles/hljs/default-style';
declare module 'react-syntax-highlighter/dist/cjs/default-highlight';
declare module 'react-syntax-highlighter/dist/cjs/create-element' {
  export function createStyleObject(
    classNames: string[],
    elementStyle: Record<string, unknown>,
    stylesheet: Record<string, Record<string, unknown>>,
  ): Record<string, any>;
}
