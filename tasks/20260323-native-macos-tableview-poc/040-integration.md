# ChatPane Integration

**Parent Task:** `tasks/20260323-native-macos-tableview-poc/000-main.md`
**Depends On:** `tasks/20260323-native-macos-tableview-poc/030-variable-height.md`

## Goal

Wire the NativeMessageList component into ChatPane for real-world testing with actual message data.

## Integration Strategy

### Step 1: Feature Flag

Add a toggle in ChatPane to switch between native and ScrollView implementations:

```typescript
// ChatPane.tsx near top
const USE_NATIVE_MESSAGE_LIST = __DEV__ && Platform.OS === 'macos';
```

### Step 2: Data Transformation

Messages in ChatPane use a complex structure. Create a transform function:

```typescript
// Convert internal message format to native table format
const transformMessagesForNative = (messages: ChatMessage[]): NativeMessage[] => {
  return messages.map(m => ({
    id: m.message_id || m.id,
    // For POC: just send content preview, not full render
    content: m.content?.substring(0, 200) || '',
    type: m.role, // 'user' | 'assistant' | 'tool'
    hasAttachments: !!(m.multipartContent?.length),
  }));
};
```

### Step 3: Conditional Rendering

Replace the existing ScrollView message list section (around lines 2600-2700):

```typescript
{USE_NATIVE_MESSAGE_LIST ? (
  <NativeMessageList
    data={transformMessagesForNative(displayMessages)}
    heights={messageHeights} // From subtask 030
    onRowPress={handleMessagePress}
    style={styles.messageList}
  />
) : (
  // Existing ScrollView implementation
  <ScrollView ...>
    {displayMessages.map(...)}
  </ScrollView>
)}
```

### Step 4: Event Handling

Connect native callbacks to existing handlers:

```typescript
const handleMessagePress = useCallback((messageId: string) => {
  // Find message in displayMessages
  const message = displayMessages.find(m => (m.message_id || m.id) === messageId);
  if (message) {
    // Call existing message selection handler
    onSelectMessage?.(message);
  }
}, [displayMessages, onSelectMessage]);
```

## Simplified POC Scope

For proof-of-concept, limit scope:

1. **Read-only display** - No inline editing, reactions, etc.
2. **Text preview only** - Show message.content substring, not full markdown rendering
3. **No sticky headers** - Skip date separators for now
4. **Static list** - Updates when new messages arrive, but no complex animations

## Testing Checklist

### Performance
- [ ] Smooth 60fps scroll with 500+ messages
- [ ] Memory usage under 100MB for 1000 messages
- [ ] No JS thread blocking during scroll

### Functionality
- [ ] All messages display (no truncation)
- [ ] Row heights visually correct (no overlaps)
- [ ] Tap on row triggers correct message
- [ ] Scroll position maintained when new messages arrive

### Comparison
- [ ] Side-by-side with ScrollView feels smoother
- [ ] Scrollbar thumb size reflects actual scrollable area
- [ ] No visual jumps or flickers

## Known Limitations (Acceptable for POC)

1. **No rich rendering** - Plain text preview instead of full markdown
2. **No inline actions** - Long-press menu, reactions not implemented
3. **No accessibility** - VoiceOver not tested
4. **No RTL** - Right-to-left text not handled

## Success Criteria

The POC is successful if:
1. Native table renders 500+ messages with smooth scroll
2. Variable heights don't cause layout issues
3. Can be toggled on/off without breaking existing ScrollView
4. Performance is measurably better (use React DevTools Profiler)

## Deliverables

1. NativeMessageList integrated into ChatPane behind feature flag
2. Data transformation layer working
3. Basic event handling connected
4. Performance comparison documented
