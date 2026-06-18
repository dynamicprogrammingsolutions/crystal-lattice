import React from 'react';
import {
  Platform,
  StyleSheet,
  Text,
  TextInput,
  type StyleProp,
  type TextStyle,
} from 'react-native';

interface SelectablePlainTextProps {
  text?: string;
  children?: React.ReactNode;
  style?: StyleProp<TextStyle>;
  numberOfLines?: number;
  testID?: string;
}

function resolveText(text: string | undefined, children: React.ReactNode): string {
  if (text != null) return text;
  if (typeof children === 'string' || typeof children === 'number') return String(children);
  if (Array.isArray(children)) {
    return children
      .map((child) => {
        if (typeof child === 'string' || typeof child === 'number') return String(child);
        return '';
      })
      .join('');
  }
  return '';
}

const SelectablePlainText: React.FC<SelectablePlainTextProps> = ({
  text,
  children,
  style,
  numberOfLines,
  testID,
}) => {
  const content = resolveText(text, children);

  if (Platform.OS === 'ios') {
    return (
      <TextInput
        style={[styles.inputReset, style]}
        value={content}
        editable={false}
        multiline
        scrollEnabled={false}
        showSoftInputOnFocus={false}
        numberOfLines={numberOfLines}
        testID={testID}
      />
    );
  }

  return (
    <Text
      style={style}
      selectable
      numberOfLines={numberOfLines}
      testID={testID}
    >
      {content}
    </Text>
  );
};

const styles = StyleSheet.create({
  inputReset: {
    paddingTop: 0,
    paddingBottom: 0,
    paddingLeft: 0,
    paddingRight: 0,
    margin: 0,
    borderWidth: 0,
    backgroundColor: 'transparent',
  },
});

export default SelectablePlainText;