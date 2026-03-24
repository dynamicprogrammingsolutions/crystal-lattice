# Research: Current Message List and NSTableView Integration

**Parent Task:** `tasks/20260323-native-macos-tableview-poc/000-main.md`

## Research Goals

1. Understand current ChatPane message list implementation
2. Analyze DesktopMessageBubble structure and height variability
3. Research NSTableView integration patterns in react-native-macos
4. Identify existing native modules in the project for reference

## Current Implementation Analysis

### ChatPane Message List (desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx)

The message list currently uses a ScrollView with manual rendering. Key areas to examine:
- Lines ~2600-2700: ScrollView setup and message rendering loop
- Message data structure and key extraction
- onLayout handlers for scroll persistence

### DesktopMessageBubble (desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx)

Variable height sources:
- Markdown content rendering with different block types
- Tool results with collapsible sections
- Reasoning sections
- Attachment thumbnails
- Code blocks

Height varies from ~50px (short text) to ~500px+ (long content).

## NSTableView Integration Research

### Key Concepts
- `NSTableView` uses a data source pattern (numberOfRows, viewForTableColumn)
- `NSTableViewDelegate` for height calculations (`tableView:heightOfRow:`)
- Cell reuse via `makeViewWithIdentifier:owner:`

### React Native Bridge Patterns
- RCTViewManager subclass
- RCTBridgeModule for method exports
- Event dispatcher for callbacks (onPress, onHover)

## Existing Native Modules Reference

Check these files for project-specific patterns:
- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm` - Existing RCTViewManager
- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacScrollViewMetrics.swift` (if exists) - Scroll measurement patterns

## Deliverables

1. Document current ChatPane message list architecture
2. List variable-height factors in DesktopMessageBubble
3. Identify NSTableView integration approach for this codebase
4. Note any existing height measurement patterns from SessionsPanel work

## Related Work

The SessionsPanel sliding window implementation (lines ~400-450 in SessionsPanel.tsx) shows:
- How `rowLayoutsRef` tracks actual row heights via onLayout
- How `getMacScrollViewMetrics` gets native scroll position
- This pattern may inform the native module design
