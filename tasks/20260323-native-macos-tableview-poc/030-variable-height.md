# Variable Height Row Strategy

**Parent Task:** `tasks/20260323-native-macos-tableview-poc/000-main.md`
**Depends On:** `tasks/20260323-native-macos-tableview-poc/020-native-module.md`

## Problem

Message bubbles have variable heights:
- Short text: ~50px
- Code blocks: ~200px
- Tool results: ~150px
- Attachments: varies

NSTableView requires `tableView:heightOfRow:` to return exact height before cell creation.

## Solution Options

### Option A: Measure-Cache-Lookup (Recommended for POC)

1. **Initial Render:**
   - Render all cells with estimated height (~100px)
   - Measure actual heights after mount
   - Store in `[rowKey: height]` cache

2. **Subsequent Renders:**
   - Check cache first in `heightOfRow:`
   - Return cached height if available
   - Return estimate if not cached

3. **Height Update:**
   - After measuring, call `tableView.noteHeightOfRows(changedRows)`
   - NSTableView animates to new positions

```objc
// Height cache
@property (nonatomic, strong) NSMutableDictionary<NSString *, NSNumber *> *heightCache;

- (CGFloat)tableView:(NSTableView *)tableView heightOfRow:(NSInteger)row {
  NSString *key = self.data[row][@"message_id"];
  NSNumber *cached = self.heightCache[key];
  return cached ? cached.doubleValue : 100.0; // default estimate
}
```

### Option B: Native Cell Self-Sizing

Use `NSTableViewRowSizeStyleCustom` and let cells size themselves:
```objc
cell.rowSizeStyle = NSTableViewRowSizeStyleCustom;
// Cell calculates its own fitting size
```

**Pros:** No manual height cache
**Cons:** Slower, NSTableView recalculates often, choppy scroll

### Option C: Fixed-Height Rows (Not Viable)

Truncate/expand all messages to uniform height.
**Rejected:** Poor UX for message content

## POC Implementation Plan

### Step 1: Height Cache
Add to RCTMessageListViewManager:
```objc
@interface RCTMessageListViewManager ()
@property (nonatomic, strong) NSMutableDictionary<NSString *, NSNumber *> *heightCache;
@property (nonatomic, strong) NSMutableSet<NSString *> *pendingMeasurement;
@end
```

### Step 2: Bridge for Measurement
JS sends message content → Native renders off-screen → Measures → Returns height

```objc
RCT_EXPORT_METHOD(measureRow:(NSString *)content 
                  messageId:(NSString *)messageId
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject) {
  // Create cell off-screen
  // Size to fit
  // Return height
  resolve(@{@"height": @(height)});
}
```

### Step 3: Batch Measurement
For POC with 100 messages:
- Measure first 20 visible immediately
- Queue remaining 80 for background measurement
- Update cache as measurements complete
- Call `noteHeightOfRows` for incremental updates

### Step 4: React Integration
```typescript
const [heights, setHeights] = useState<Record<string, number>>({});

useEffect(() => {
  // Measure all messages once
  Promise.all(messages.map(m => NativeModules.MessageList.measureRow(m.content, m.id)))
    .then(results => {
      const heightMap = {};
      results.forEach((r, i) => heightMap[messages[i].id] = r.height);
      setHeights(heightMap);
    });
}, [messages]);

<NativeMessageList data={messages} heights={heights} />
```

## Alternative: Hybrid Approach

For POC simplicity, combine Options A + C:
- Use fixed height for text-only messages (80px)
- Use estimated height for complex messages (200px)
- Measure actual heights lazily as user scrolls

This proves the concept without complex measurement infrastructure.

## Deliverables

1. Height cache implemented in native module
2. Basic measurement strategy working (can be simplified)
3. Table renders with approximately correct row heights
4. Scroll is smooth without jumps

## Testing

Create messages with varying content:
```javascript
const testMessages = [
  { id: '1', content: 'Short', type: 'text' },           // ~50px
  { id: '2', content: '# Markdown\n\n```code```', type: 'markdown' }, // ~200px
  { id: '3', content: 'Tool result...', type: 'tool' },   // ~150px
  // ... 100 items
];
```

Verify:
- No row overlaps or gaps
- Scrollbar thumb size is roughly correct
- No visible height recalculations during scroll
