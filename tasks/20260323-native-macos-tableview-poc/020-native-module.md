# Create Native Module Skeleton

**Parent Task:** `tasks/20260323-native-macos-tableview-poc/000-main.md`
**Depends On:** `tasks/20260323-native-macos-tableview-poc/010-research.md`

## Goal

Create a minimal RCTViewManager subclass that wraps NSTableView and exposes it to React Native.

## Files to Create

### 1. Header File
`desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/RCTMessageListViewManager.h`

```objc
#import <React/RCTViewManager.h>

@interface RCTMessageListViewManager : RCTViewManager
@end
```

### 2. Implementation File
`desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/RCTMessageListViewManager.m`

Basic structure:
- Subclass RCTViewManager
- Return NSTableView from view method
- Implement data source (numberOfRows, viewForTableColumn)
- Accept `data` prop as array of message objects
- Accept `renderItem` as a callback (or simplify for POC)

### 3. JS Bridge Component
`desktop/crystal-lattice-control-desktop-rn/src/chat/NativeMessageList.tsx`

```typescript
import { requireNativeComponent } from 'react-native';

interface NativeMessageListProps {
  data: any[];
  onRowPress?: (key: string) => void;
  // Simplified for POC - just prove native table works
}

export const NativeMessageList = requireNativeComponent('RCTMessageListView');
```

## Key Implementation Details

### NSTableView Setup
```objc
- (NSView *)view {
  NSTableView *tableView = [[NSTableView alloc] init];
  tableView.dataSource = self;
  tableView.delegate = self;
  
  // Single column for message list
  NSTableColumn *column = [[NSTableColumn alloc] initWithIdentifier:@"message"];
  [tableView addTableColumn:column];
  
  return tableView;
}
```

### Data Source Methods
```objc
- (NSInteger)numberOfRowsInTableView:(NSTableView *)tableView {
  return self.data.count; // self.data from RN props
}

- (NSView *)tableView:(NSTableView *)tableView 
   viewForTableColumn:(NSTableColumn *)tableColumn 
                  row:(NSInteger)row {
  // For POC: Return a simple NSTextField with message preview
  // Full implementation in subtask 030
}
```

### Props Bridge
```objc
RCT_EXPORT_VIEW_PROPERTY(data, NSArray)
RCT_EXPORT_VIEW_PROPERTY(onRowPress, RCTBubblingEventBlock)
```

## POC Scope Limitations

For this subtask:
- Render simple NSTextField cells (not full React content)
- Just prove data flows from JS to native and table renders
- Variable height and React content handled in subtask 030

## Testing

Create a test view in ChatPane (behind a __DEV__ flag):
```typescript
{__DEV__ && (
  <NativeMessageList 
    data={messages.slice(0, 100)} 
    style={{flex: 1}}
  />
)}
```

Verify:
- 100 rows render
- Table view appears in hierarchy
- Scrolls without JS thread blocking

## Deliverables

1. Three files created (header, implementation, JS bridge)
2. Registered with RCTViewManager
3. Renders basic native cells with mock data
4. Proof that native virtualization works (check Instruments for low memory)
