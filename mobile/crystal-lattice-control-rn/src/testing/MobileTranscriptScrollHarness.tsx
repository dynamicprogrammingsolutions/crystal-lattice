import React from "react";
import { StyleSheet, Text, View, type FlatList } from "react-native";

import { InvertedTranscriptViewport } from "../components/InvertedTranscriptViewport";
import { ThemeProvider, lightTheme } from "../theme";

type HarnessMessage = {
  index: number;
  content: string;
};

const MESSAGE_COUNT = 300;

const HARNESS_MESSAGES: HarnessMessage[] = Array.from(
  { length: MESSAGE_COUNT },
  (_, index) => {
    const lineCount = 1 + (index % 8);
    const lines = Array.from(
      { length: lineCount },
      (_unused, lineIndex) =>
        `Message ${index}, line ${
          lineIndex + 1
        }: deterministic transcript content.`
    );
    return {
      index,
      content: lines.join("\n"),
    };
  }
).reverse();

export function MobileTranscriptScrollHarness(): React.JSX.Element {
  const listRef = React.useRef<FlatList<any> | null>(null);

  return (
    <ThemeProvider theme={lightTheme}>
      <View style={styles.root} testID="transcript-harness-ready">
        <InvertedTranscriptViewport
          listRef={listRef}
          data={HARNESS_MESSAGES}
          testID="transcript-scroll-list"
          initialScrollAnchor={{
            bottomGapPx: 0,
            pinnedToBottom: true,
            updatedAtMs: 1,
          }}
          keyExtractor={(message) => String(message.index)}
          getItemDependencies={(message) => [message.content]}
          renderItem={({ item: message }) => (
            <View
              collapsable={false}
              style={styles.message}
              testID={`transcript-message-${message.index}`}
            >
              <Text style={styles.messageIndex}>Message {message.index}</Text>
              <Text style={styles.messageContent}>{message.content}</Text>
            </View>
          )}
        />
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  message: {
    marginHorizontal: 10,
    marginVertical: 5,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D1D6",
    backgroundColor: "#FFFFFF",
  },
  messageIndex: {
    marginBottom: 4,
    color: "#000000",
    fontSize: 13,
    fontWeight: "700",
  },
  messageContent: {
    color: "#000000",
    fontSize: 14,
  },
});
