#import <Cocoa/Cocoa.h>

#import <math.h>

#import <React/RCTComponent.h>
#import <React/RCTConvert.h>
#import <React/RCTUIManager.h>
#import <React/RCTViewManager.h>

@interface CLCMacPassthroughLabel : NSTextField
@end

@implementation CLCMacPassthroughLabel

- (NSView *)hitTest:(__unused NSPoint)point
{
  return nil;
}

@end

@interface CLCMacTextView : NSView <NSTextViewDelegate>

@property(nonatomic, copy) RCTBubblingEventBlock onChange;
@property(nonatomic, copy) RCTBubblingEventBlock onSubmit;
@property(nonatomic, copy) RCTBubblingEventBlock onMacContentSizeChange;

@property(nonatomic, copy) NSString *value;
@property(nonatomic, copy) NSString *initialText;
@property(nonatomic, copy) NSString *placeholder;
@property(nonatomic, assign) BOOL editable;

@property(nonatomic, assign) BOOL autoGrow;
@property(nonatomic, assign) CGFloat maxHeight;

@property(nonatomic, strong) NSColor *textColor;
@property(nonatomic, strong) NSColor *placeholderTextColor;
@property(nonatomic, assign) CGFloat fontSize;

- (void)setTextInternal:(NSString *)text markEdited:(BOOL)markEdited;
- (void)focusInput;

@end

@implementation CLCMacTextView {
  NSScrollView *_scrollView;
  NSTextView *_textView;
  NSTextField *_placeholderLabel;
  BOOL _settingText;
  BOOL _hasUserEdited;
  CGFloat _lastContentHeight;
}

- (instancetype)initWithFrame:(NSRect)frame
{
  if ((self = [super initWithFrame:frame])) {
    self.wantsLayer = YES;

    _scrollView = [[NSScrollView alloc] initWithFrame:NSZeroRect];
    _scrollView.translatesAutoresizingMaskIntoConstraints = NO;
    _scrollView.drawsBackground = NO;
    _scrollView.borderType = NSNoBorder;
    _scrollView.hasHorizontalScroller = NO;
    _scrollView.hasVerticalScroller = NO;
    _scrollView.autohidesScrollers = YES;

    _textView = [[NSTextView alloc] initWithFrame:NSZeroRect];
    // NSTextView is embedded as the scroll view's documentView; sizing is handled in `layout`.
    _textView.translatesAutoresizingMaskIntoConstraints = YES;
    _textView.autoresizingMask = NSViewWidthSizable;
    _textView.delegate = self;
    _textView.drawsBackground = NO;
    _textView.focusRingType = NSFocusRingTypeNone;
    _textView.usesFindBar = NO;
    _textView.richText = NO;
    _textView.importsGraphics = NO;
    _textView.allowsUndo = YES;
    _textView.automaticQuoteSubstitutionEnabled = NO;
    _textView.automaticDashSubstitutionEnabled = NO;
    _textView.automaticTextReplacementEnabled = NO;
    _textView.automaticSpellingCorrectionEnabled = NO;
    _textView.continuousSpellCheckingEnabled = NO;
    _textView.grammarCheckingEnabled = NO;
    _textView.textContainerInset = NSMakeSize(8, 8);
    _textView.textContainer.lineFragmentPadding = 0;
    _textView.maxSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    _textView.verticallyResizable = YES;
    _textView.horizontallyResizable = NO;
    _textView.textContainer.containerSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    _textView.textContainer.widthTracksTextView = YES;

    _scrollView.documentView = _textView;

    _placeholderLabel = [[CLCMacPassthroughLabel alloc] initWithFrame:NSZeroRect];
    _placeholderLabel.translatesAutoresizingMaskIntoConstraints = NO;
    _placeholderLabel.bezeled = NO;
    _placeholderLabel.drawsBackground = NO;
    _placeholderLabel.editable = NO;
    _placeholderLabel.selectable = NO;
    _placeholderLabel.lineBreakMode = NSLineBreakByTruncatingTail;
    _placeholderLabel.maximumNumberOfLines = 1;
    _placeholderLabel.hidden = YES;

    [self addSubview:_scrollView];
    [self addSubview:_placeholderLabel];

    [NSLayoutConstraint activateConstraints:@[
      [_scrollView.leadingAnchor constraintEqualToAnchor:self.leadingAnchor],
      [_scrollView.trailingAnchor constraintEqualToAnchor:self.trailingAnchor],
      [_scrollView.topAnchor constraintEqualToAnchor:self.topAnchor],
      [_scrollView.bottomAnchor constraintEqualToAnchor:self.bottomAnchor],
      [_placeholderLabel.leadingAnchor constraintEqualToAnchor:self.leadingAnchor constant:8],
      [_placeholderLabel.topAnchor constraintEqualToAnchor:self.topAnchor constant:8],
      [_placeholderLabel.trailingAnchor constraintLessThanOrEqualToAnchor:self.trailingAnchor constant:-8],
    ]];

    self.value = @"";
    self.initialText = nil;
    self.placeholder = @"";
    self.editable = YES;
    self.autoGrow = NO;
    self.maxHeight = 0;
    self.textColor = [NSColor labelColor];
    self.placeholderTextColor = [NSColor placeholderTextColor];
    self.fontSize = 13;
  }
  return self;
}

- (void)layout
{
  [super layout];

  // Keep the document view sized to the scroll view's visible width.
  // Without this, the NSTextView may end up with a 0x0 frame and never receive clicks.
  NSRect bounds = _scrollView.contentView.bounds;
  if (!isfinite(bounds.size.width) || bounds.size.width <= 0) {
    return;
  }
  _textView.frame = NSMakeRect(0, 0, bounds.size.width, bounds.size.height);
  _textView.textContainer.containerSize = NSMakeSize(bounds.size.width, CGFLOAT_MAX);
  _textView.textContainer.widthTracksTextView = YES;

  [self updateContentSizeIfNeeded];
}

- (BOOL)acceptsFirstResponder
{
  return YES;
}

- (BOOL)becomeFirstResponder
{
  return [_textView becomeFirstResponder];
}

- (BOOL)acceptsFirstMouse:(__unused NSEvent *)event
{
  return YES;
}

- (NSView *)hitTest:(NSPoint)point
{
  NSView *hit = [super hitTest:point];

  // Route pointer events to the NSTextView so it can manage selection/caret
  // without React Native swallowing the click.
  if (hit == self || hit == _scrollView || hit == _scrollView.contentView) {
    return _textView;
  }
  return hit;
}

- (void)mouseDown:(NSEvent *)event
{
  [self focusInput];
  [_textView mouseDown:event];
}

- (void)mouseDragged:(NSEvent *)event
{
  [_textView mouseDragged:event];
}

- (void)mouseUp:(NSEvent *)event
{
  [_textView mouseUp:event];
}

- (void)setValue:(NSString *)value
{
  // `value` exists for compatibility, but this component should not be used
  // as a continuously-controlled input. Prefer `initialText` + the imperative
  // `setText` method for programmatic updates.
  [self setTextInternal:(value ?: @"") markEdited:NO];
}

- (void)setInitialText:(NSString *)initialText
{
  _initialText = [initialText copy];
  if (_hasUserEdited) {
    return;
  }
  if (_initialText == nil) {
    return;
  }
  [self setTextInternal:_initialText markEdited:NO];
}

- (void)setTextInternal:(NSString *)text markEdited:(BOOL)markEdited
{
  NSString *next = text ?: @"";
  if ([_textView.string isEqualToString:next]) {
    return;
  }

  _settingText = YES;
  _textView.string = next;
  _settingText = NO;
  _value = [next copy];
  if (markEdited) {
    _hasUserEdited = YES;
  }
  [self updatePlaceholderVisibility];
  [self updateContentSizeIfNeeded];
}

- (void)focusInput
{
  [[self window] makeFirstResponder:_textView];
}

- (void)setPlaceholder:(NSString *)placeholder
{
  _placeholder = [placeholder ?: @"" copy];
  _placeholderLabel.stringValue = _placeholder;
  [self updatePlaceholderVisibility];
}

- (void)setEditable:(BOOL)editable
{
  _editable = editable;
  _textView.editable = editable;
  _textView.selectable = YES;
  _textView.textColor = self.textColor;
  _textView.insertionPointColor = self.textColor;
}

- (void)setTextColor:(NSColor *)textColor
{
  _textColor = textColor ?: [NSColor labelColor];
  _textView.textColor = _textColor;
  _textView.insertionPointColor = _textColor;
}

- (void)setPlaceholderTextColor:(NSColor *)placeholderTextColor
{
  _placeholderTextColor = placeholderTextColor ?: [NSColor placeholderTextColor];
  _placeholderLabel.textColor = _placeholderTextColor;
}

- (void)setFontSize:(CGFloat)fontSize
{
  _fontSize = fontSize > 0 ? fontSize : 13;
  _textView.font = [NSFont systemFontOfSize:_fontSize];
  _placeholderLabel.font = [NSFont systemFontOfSize:_fontSize];
}

- (void)setAutoGrow:(BOOL)autoGrow
{
  _autoGrow = autoGrow;
  [self updateContentSizeIfNeeded];
}

- (void)setMaxHeight:(CGFloat)maxHeight
{
  _maxHeight = maxHeight;
  [self updateContentSizeIfNeeded];
}

- (void)updatePlaceholderVisibility
{
  BOOL hasText = _textView.string.length > 0;
  BOOL hasPlaceholder = _placeholder.length > 0;
  _placeholderLabel.hidden = hasText || !hasPlaceholder;
}

- (CGFloat)calculateContentHeight
{
  NSLayoutManager *layoutManager = _textView.layoutManager;
  NSTextContainer *container = _textView.textContainer;
  if (!layoutManager || !container) {
    return 0;
  }

  [layoutManager ensureLayoutForTextContainer:container];
  NSRect used = [layoutManager usedRectForTextContainer:container];
  CGFloat inset = _textView.textContainerInset.height * 2;
  CGFloat height = ceil(used.size.height + inset);
  return MAX(0, height);
}

- (void)updateContentSizeIfNeeded
{
  NSRect bounds = _scrollView.contentView.bounds;
  if (!isfinite(bounds.size.width) || bounds.size.width <= 1) {
    return;
  }

  // Keep the text container width in sync with the visible width so
  // measurement remains stable during React layout passes.
  _textView.textContainer.containerSize = NSMakeSize(bounds.size.width, CGFLOAT_MAX);
  _textView.textContainer.widthTracksTextView = YES;

  CGFloat height = [self calculateContentHeight];
  if (!isfinite(height)) {
    return;
  }

  // Ignore transient measurements where the text hasn't laid out yet.
  // When that happens, `usedRect` can be 0 and the height collapses to just
  // the inset (~16px). That causes JS auto-grow to oscillate.
  CGFloat insetBaseline = ceil(_textView.textContainerInset.height * 2);
  BOOL hasText = _textView.string.length > 0;
  if (hasText && height <= insetBaseline + 1 && _lastContentHeight > insetBaseline + 8) {
    return;
  }

  // Ensure the document view reflects the full content height so scrolling works
  // when the outer React Native view is capped.
  CGFloat visibleHeight = isfinite(bounds.size.height) ? bounds.size.height : 0;
  CGFloat docHeight = MAX(height, visibleHeight);
  if (isfinite(bounds.size.width) && bounds.size.width > 0) {
    NSRect frame = _textView.frame;
    BOOL needsResize = fabs(frame.size.height - docHeight) >= 0.5 || fabs(frame.size.width - bounds.size.width) >= 0.5;
    if (needsResize) {
      frame.size.width = bounds.size.width;
      frame.size.height = docHeight;
      _textView.frame = frame;
    }
  }

  if (fabs(height - _lastContentHeight) < 0.5) {
    return;
  }
  _lastContentHeight = height;

  if (_autoGrow && _maxHeight > 0) {
    BOOL shouldScroll = height > _maxHeight + 0.5;
    _scrollView.hasVerticalScroller = shouldScroll;
  } else {
    _scrollView.hasVerticalScroller = NO;
  }

  if (self.onMacContentSizeChange) {
    NSUInteger textLength = _textView.string.length;
    self.onMacContentSizeChange(@{
      @"contentSize" : @{ @"width" : @(0), @"height" : @(height) },
      @"textLength" : @(textLength),
    });
  }
}

- (void)textDidChange:(NSNotification *)notification
{
  if (notification.object != _textView) {
    return;
  }

  [self updatePlaceholderVisibility];
  [self updateContentSizeIfNeeded];

  if (_settingText) {
    return;
  }

  NSString *text = _textView.string ?: @"";
  _value = [text copy];
  _hasUserEdited = YES;

  if (self.onChange) {
    self.onChange(@{ @"text" : text });
  }
}

- (BOOL)textView:(NSTextView *)textView doCommandBySelector:(SEL)commandSelector
{
  if (textView != _textView) {
    return NO;
  }

  if (commandSelector == @selector(insertNewline:) ||
      commandSelector == @selector(insertNewlineIgnoringFieldEditor:)) {
    NSEvent *event = [NSApp currentEvent];
    BOOL shift = (event.modifierFlags & NSEventModifierFlagShift) != 0;

    // Hardcoded behavior (for now): Enter sends, Shift+Enter inserts newline.
    if (!shift) {
      if (self.onSubmit) {
        self.onSubmit(@{ @"text" : (_textView.string ?: @"") });
      }
      return YES;
    }
  }

  return NO;
}

@end

@interface MacTextViewManager : RCTViewManager
@end

@implementation MacTextViewManager

RCT_EXPORT_MODULE(MacTextView)

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSView *)view
{
  return [[CLCMacTextView alloc] initWithFrame:NSZeroRect];
}

RCT_EXPORT_METHOD(setText:(nonnull NSNumber *)reactTag text:(NSString *)text)
{
  [self.bridge.uiManager addUIBlock:^(__unused RCTUIManager *uiManager, NSDictionary<NSNumber *, NSView *> *viewRegistry) {
    NSView *view = viewRegistry[reactTag];
    if (![view isKindOfClass:[CLCMacTextView class]]) {
      return;
    }
    CLCMacTextView *textView = (CLCMacTextView *)view;
    [textView setTextInternal:text markEdited:NO];
  }];
}

RCT_EXPORT_METHOD(focus:(nonnull NSNumber *)reactTag)
{
  [self.bridge.uiManager addUIBlock:^(__unused RCTUIManager *uiManager, NSDictionary<NSNumber *, NSView *> *viewRegistry) {
    NSView *view = viewRegistry[reactTag];
    if (![view isKindOfClass:[CLCMacTextView class]]) {
      return;
    }
    CLCMacTextView *textView = (CLCMacTextView *)view;
    [textView focusInput];
  }];
}

RCT_EXPORT_VIEW_PROPERTY(onChange, RCTBubblingEventBlock)
RCT_EXPORT_VIEW_PROPERTY(onSubmit, RCTBubblingEventBlock)
RCT_EXPORT_VIEW_PROPERTY(onMacContentSizeChange, RCTBubblingEventBlock)

RCT_CUSTOM_VIEW_PROPERTY(initialText, NSString, CLCMacTextView)
{
  view.initialText = json ? [RCTConvert NSString:json] : nil;
}

RCT_CUSTOM_VIEW_PROPERTY(placeholder, NSString, CLCMacTextView)
{
  view.placeholder = json ? [RCTConvert NSString:json] : @"";
}

RCT_CUSTOM_VIEW_PROPERTY(editable, BOOL, CLCMacTextView)
{
  view.editable = json ? [RCTConvert BOOL:json] : YES;
}

RCT_CUSTOM_VIEW_PROPERTY(autoGrow, BOOL, CLCMacTextView)
{
  view.autoGrow = json ? [RCTConvert BOOL:json] : NO;
}

RCT_CUSTOM_VIEW_PROPERTY(maxHeight, CGFloat, CLCMacTextView)
{
  view.maxHeight = json ? [RCTConvert CGFloat:json] : 0;
}

RCT_CUSTOM_VIEW_PROPERTY(textColor, NSColor, CLCMacTextView)
{
  view.textColor = json ? [RCTConvert NSColor:json] : [NSColor labelColor];
}

RCT_CUSTOM_VIEW_PROPERTY(placeholderTextColor, NSColor, CLCMacTextView)
{
  view.placeholderTextColor = json ? [RCTConvert NSColor:json] : [NSColor placeholderTextColor];
}

RCT_CUSTOM_VIEW_PROPERTY(fontSize, CGFloat, CLCMacTextView)
{
  view.fontSize = json ? [RCTConvert CGFloat:json] : 13;
}

@end
