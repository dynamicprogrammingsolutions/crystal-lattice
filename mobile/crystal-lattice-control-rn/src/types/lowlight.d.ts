declare module 'lowlight' {
  export type LowlightTextNode = {
    type: 'text';
    value: string;
  };

  export type LowlightElementNode = {
    type: 'element';
    tagName: string;
    properties?: {
      className?: string[];
    };
    children?: LowlightNode[];
  };

  export type LowlightNode = LowlightTextNode | LowlightElementNode;

  export type LowlightResult = {
    relevance: number;
    language: string;
    value: LowlightNode[];
    secondBest?: LowlightResult | null;
  };

  const lowlight: {
    getLanguage(language: string): unknown;
    highlight(language: string, value: string): LowlightResult;
    highlightAuto(value: string): LowlightResult;
  };

  export default lowlight;
}