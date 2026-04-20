#ifdef RCT_NEW_ARCH_ENABLED

#import <Cocoa/Cocoa.h>

#import <math.h>

#import <React/RCTConversions.h>
#import <React/RCTComponentViewProtocol.h>
#import <React/RCTFabricComponentsPlugins.h>
#import <React/RCTViewComponentView.h>

#import <react/renderer/components/CLCMacTextViewSpec/ComponentDescriptors.h>
#import <react/renderer/components/CLCMacTextViewSpec/EventEmitters.h>
#import <react/renderer/components/CLCMacTextViewSpec/Props.h>
#import <react/renderer/components/CLCMacTextViewSpec/RCTComponentViewHelpers.h>

using namespace facebook::react;

@interface CLCMacPassthroughLabel : NSTextField
@end

@implementation CLCMacPassthroughLabel

- (NSView *)hitTest:(__unused NSPoint)point
{
  return nil;
}

@end

@interface CLCMacBackingTextView : NSTextView

@property(nonatomic, weak) id owner;

@end

@implementation CLCMacBackingTextView

- (void)toggleAutomaticSpellingCorrection:(id)__unused sender
{
  self.automaticSpellingCorrectionEnabled = !self.isAutomaticSpellingCorrectionEnabled;
}

- (void)toggleContinuousSpellChecking:(id)__unused sender
{
  self.continuousSpellCheckingEnabled = !self.isContinuousSpellCheckingEnabled;
}

- (void)toggleGrammarChecking:(id)__unused sender
{
  self.grammarCheckingEnabled = !self.isGrammarCheckingEnabled;
}

- (void)setEnabledTextCheckingTypes:(NSTextCheckingTypes)checkingType
{
  [super setEnabledTextCheckingTypes:checkingType];
  self.automaticDataDetectionEnabled = checkingType != 0;
}

- (void)showGuessPanel:(id)sender
{
  if ([self.owner respondsToSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)]) {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Warc-performSelector-leaks"
    [self.owner performSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)];
#pragma clang diagnostic pop
  }
  [super showGuessPanel:sender];
}

- (void)orderFrontSubstitutionsPanel:(id)sender
{
  if ([self.owner respondsToSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)]) {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Warc-performSelector-leaks"
    [self.owner performSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)];
#pragma clang diagnostic pop
  }
  [super orderFrontSubstitutionsPanel:sender];
}

- (void)checkSpelling:(id)sender
{
  if ([self.owner respondsToSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)]) {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Warc-performSelector-leaks"
    [self.owner performSelector:@selector(userDidExplicitlyRequestManagedSpellPanels)];
#pragma clang diagnostic pop
  }
  [super checkSpelling:sender];
}

@end

@interface CLCMacTextViewContentView : NSView <NSTextViewDelegate>

@property(nonatomic, copy) void (^onChangeText)(NSString *text);
@property(nonatomic, copy) void (^onSubmitText)(NSString *text);
@property(nonatomic, copy) void (^onContentHeightChange)(CGFloat width, CGFloat height, NSInteger textLength);

@property(nonatomic, copy) NSString *initialText;
@property(nonatomic, copy) NSString *placeholder;
@property(nonatomic, assign, getter=isEditable) BOOL editable;
@property(nonatomic, assign) BOOL autoGrow;
@property(nonatomic, assign) CGFloat maxHeight;
@property(nonatomic, strong) NSColor *textColor;
@property(nonatomic, strong) NSColor *placeholderTextColor;
@property(nonatomic, assign) CGFloat fontSize;

- (void)setTextProgrammatically:(NSString *)text;
- (void)focusInput;
- (void)resetForRecycle;
- (void)userDidExplicitlyRequestManagedSpellPanels;

@end

@implementation CLCMacTextViewContentView {
  NSScrollView *_scrollView;
  NSTextView *_textView;
  NSTextField *_placeholderLabel;
  NSTextStorage *_measurementTextStorage;
  NSLayoutManager *_measurementLayoutManager;
  NSTextContainer *_measurementTextContainer;
  BOOL _settingText;
  BOOL _hasUserEdited;
  BOOL _measureScheduled;
  BOOL _needsMeasureAfterLayout;
  BOOL _forceComplexMeasurement;
  BOOL _suppressesSpellPanelsAfterActivation;
  CGFloat _lastAvailableWidth;
  CGFloat _lastContentHeight;
}

- (BOOL)isManagedSpellPanelWindow:(NSWindow *)window
{
  if (window == nil) {
    return NO;
  }

  NSString *title = window.title ?: @"";
  NSString *className = NSStringFromClass(window.class) ?: @"";
  return [className isEqualToString:@"NSSpellingPanel"] ||
      [title isEqualToString:@"Languages"] ||
      [title isEqualToString:@"Spelling and Grammar"] ||
      [title isEqualToString:@"Substitutions"];
}

- (void)closeSharedSpellPanelsIfNeeded
{
  NSSpellChecker *spellChecker = [NSSpellChecker sharedSpellChecker];
  NSInteger spellDocumentTag = _textView.spellCheckerDocumentTag;

  NSPanel *spellingPanel = spellChecker.spellingPanel;
  if (spellingPanel.isVisible) {
    [spellingPanel close];
  }

  NSPanel *substitutionsPanel = spellChecker.substitutionsPanel;
  if (substitutionsPanel.isVisible) {
    [substitutionsPanel close];
  }

  for (NSWindow *window in NSApp.windows) {
    if ([self isManagedSpellPanelWindow:window]) {
      if (window.isVisible) {
        [window close];
      }
    }
  }

  if (spellDocumentTag != 0) {
    [spellChecker closeSpellDocumentWithTag:(int)spellDocumentTag];
  }

  [spellChecker updatePanels];
}

- (BOOL)hasVisibleManagedSpellPanels
{
  for (NSWindow *window in NSApp.windows) {
    if ([self isManagedSpellPanelWindow:window] && window.isVisible) {
      return YES;
    }
  }
  return NO;
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

    _textView = [[CLCMacBackingTextView alloc] initWithFrame:NSZeroRect];
    _textView.translatesAutoresizingMaskIntoConstraints = YES;
    _textView.autoresizingMask = NSViewWidthSizable;
    _textView.delegate = self;
    ((CLCMacBackingTextView *)_textView).owner = self;
    _textView.drawsBackground = NO;
    _textView.focusRingType = NSFocusRingTypeNone;
    _textView.usesFindBar = NO;
    _textView.richText = NO;
    _textView.importsGraphics = NO;
    _textView.allowsUndo = YES;
    _textView.textContainerInset = NSMakeSize(8, 8);
    _textView.textContainer.lineFragmentPadding = 0;
    _textView.maxSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    _textView.verticallyResizable = YES;
    _textView.horizontallyResizable = NO;
    _textView.textContainer.containerSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    _textView.textContainer.widthTracksTextView = YES;

    _scrollView.documentView = _textView;

    _measurementTextStorage = [[NSTextStorage alloc] initWithString:@""];
    _measurementLayoutManager = [[NSLayoutManager alloc] init];
    _measurementTextContainer =
        [[NSTextContainer alloc] initWithSize:NSMakeSize(0, CGFLOAT_MAX)];
    _measurementTextContainer.lineFragmentPadding = _textView.textContainer.lineFragmentPadding;
    [_measurementLayoutManager addTextContainer:_measurementTextContainer];
    [_measurementTextStorage addLayoutManager:_measurementLayoutManager];

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

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(handleApplicationDidBecomeActive:)
                                                 name:NSApplicationDidBecomeActiveNotification
                                               object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(handleApplicationWillResignActive:)
                                                 name:NSApplicationWillResignActiveNotification
                                               object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(handleWindowDidBecomeKey:)
                                                 name:NSWindowDidBecomeKeyNotification
                                               object:nil];

    [self resetForRecycle];
  }
  return self;
}

- (void)dealloc
{
  [[NSNotificationCenter defaultCenter] removeObserver:self];
}

- (void)resetForRecycle
{
  _settingText = NO;
  _hasUserEdited = NO;
  _measureScheduled = NO;
  _needsMeasureAfterLayout = NO;
  _forceComplexMeasurement = YES;
  _suppressesSpellPanelsAfterActivation = NO;
  _lastAvailableWidth = 0;
  _lastContentHeight = 0;
  self.initialText = @"";
  self.placeholder = @"";
  self.editable = YES;
  self.autoGrow = NO;
  self.maxHeight = 0;
  self.textColor = [NSColor labelColor];
  self.placeholderTextColor = [NSColor placeholderTextColor];
  self.fontSize = 13;
  [self setTextProgrammatically:@""];
}

- (void)userDidExplicitlyRequestManagedSpellPanels
{
  _suppressesSpellPanelsAfterActivation = NO;
}

- (void)layout
{
  [super layout];

  NSRect bounds = _scrollView.contentView.bounds;
  if (!isfinite(bounds.size.width) || bounds.size.width <= 0) {
    return;
  }

  _textView.frame = NSMakeRect(0, 0, bounds.size.width, bounds.size.height);

  CGFloat insetX = _textView.textContainerInset.width * 2;
  CGFloat availableWidth = MAX(1, bounds.size.width - insetX);
  if (fabs(_lastAvailableWidth - availableWidth) >= 0.5) {
    _lastAvailableWidth = availableWidth;
    _textView.textContainer.containerSize = NSMakeSize(availableWidth, CGFLOAT_MAX);
    _textView.textContainer.widthTracksTextView = NO;
    [_textView.layoutManager textContainerChangedGeometry:_textView.textContainer];
  }

  [self updateContentSizeIfNeeded];

  if (_needsMeasureAfterLayout && !_measureScheduled) {
    _needsMeasureAfterLayout = NO;
    [self scheduleMeasure];
  }
}

- (void)viewDidMoveToWindow
{
  [super viewDidMoveToWindow];
  [self scheduleMeasure];
}

- (BOOL)acceptsFirstResponder
{
  return _textView.acceptsFirstResponder;
}

- (NSResponder *)responder
{
  return _textView;
}

- (BOOL)becomeFirstResponder
{
  return [_textView becomeFirstResponder];
}

- (BOOL)resignFirstResponder
{
  if (_textView.selectable) {
    _textView.selectedRange = NSMakeRange(NSNotFound, 0);
  }

  BOOL success = [_textView resignFirstResponder];
  if (success) {
    [_textView breakUndoCoalescing];
    [self closeSharedSpellPanelsIfNeeded];
  }

  return success;
}

- (BOOL)acceptsFirstMouse:(__unused NSEvent *)event
{
  return YES;
}

- (NSView *)hitTest:(NSPoint)point
{
  NSView *hit = [super hitTest:point];
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

- (void)setTextProgrammatically:(NSString *)text
{
  NSString *next = text ?: @"";
  if ([_textView.string isEqualToString:next]) {
    return;
  }

  _settingText = YES;
  _textView.string = next;
  _settingText = NO;
  [self updatePlaceholderVisibility];
  [self updateContentSizeIfNeeded];

  if (!_hasUserEdited) {
    [self scheduleMeasure];
  }
}

- (void)focusInput
{
  [[self window] makeFirstResponder:self];
}

- (void)setInitialText:(NSString *)initialText
{
  _initialText = [initialText ?: @"" copy];
  if (_hasUserEdited) {
    return;
  }
  [self setTextProgrammatically:_initialText];
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

- (void)scheduleMeasure
{
  if (_measureScheduled) {
    return;
  }
  _forceComplexMeasurement = YES;
  _measureScheduled = YES;
  dispatch_async(dispatch_get_main_queue(), ^{
    self->_measureScheduled = NO;
    [self updateContentSizeIfNeeded];
  });
}

- (CGFloat)calculateContentHeightFast
{
  NSLayoutManager *layoutManager = _textView.layoutManager;
  NSTextContainer *container = _textView.textContainer;
  if (!layoutManager || !container) {
    return 0;
  }

  [layoutManager ensureLayoutForTextContainer:container];
  NSRect used = [layoutManager usedRectForTextContainer:container];
  CGFloat inset = _textView.textContainerInset.height * 2;
  return MAX(0, ceil(used.size.height + inset));
}

- (CGFloat)calculateContentHeightComplexForWidth:(CGFloat)width
{
  if (!_measurementLayoutManager || !_measurementTextContainer || !_measurementTextStorage) {
    return 0;
  }
  if (!isfinite(width) || width <= 1) {
    return 0;
  }

  _measurementTextContainer.size = NSMakeSize(width, CGFLOAT_MAX);

  NSString *text = _textView.string ?: @"";
  NSFont *font = _textView.font ?: [NSFont systemFontOfSize:_fontSize > 0 ? _fontSize : 13];
  NSDictionary<NSAttributedStringKey, id> *attrs = @{NSFontAttributeName : font};
  NSAttributedString *attributed = [[NSAttributedString alloc] initWithString:text attributes:attrs];
  [_measurementTextStorage setAttributedString:attributed];

  [_measurementLayoutManager ensureLayoutForTextContainer:_measurementTextContainer];
  NSRect used = [_measurementLayoutManager usedRectForTextContainer:_measurementTextContainer];
  CGFloat inset = _textView.textContainerInset.height * 2;
  return MAX(0, ceil(used.size.height + inset));
}

- (void)updateContentSizeIfNeeded
{
  NSRect bounds = _scrollView.contentView.bounds;
  if (!isfinite(bounds.size.width) || bounds.size.width <= 1) {
    _needsMeasureAfterLayout = YES;
    return;
  }

  CGFloat insetX = _textView.textContainerInset.width * 2;
  CGFloat availableWidth = MAX(1, bounds.size.width - insetX);
  if (fabs(_lastAvailableWidth - availableWidth) >= 0.5) {
    _lastAvailableWidth = availableWidth;
    _textView.textContainer.containerSize = NSMakeSize(availableWidth, CGFLOAT_MAX);
    _textView.textContainer.widthTracksTextView = NO;
    [_textView.layoutManager textContainerChangedGeometry:_textView.textContainer];
  }

  CGFloat height = _forceComplexMeasurement ? [self calculateContentHeightComplexForWidth:availableWidth]
                                            : [self calculateContentHeightFast];
  _forceComplexMeasurement = NO;
  if (!isfinite(height)) {
    return;
  }

  CGFloat insetBaseline = ceil(_textView.textContainerInset.height * 2);
  BOOL hasText = _textView.string.length > 0;
  if (hasText && height <= insetBaseline + 1) {
    [self scheduleMeasure];
    return;
  }

  CGFloat visibleHeight = isfinite(bounds.size.height) ? bounds.size.height : 0;
  CGFloat docHeight = MAX(height, visibleHeight);
  if (isfinite(bounds.size.width) && bounds.size.width > 0) {
    NSRect frame = _textView.frame;
    BOOL needsResize = fabs(frame.size.height - docHeight) >= 0.5 ||
        fabs(frame.size.width - bounds.size.width) >= 0.5;
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
    BOOL hadScroll = _scrollView.hasVerticalScroller;
    _scrollView.hasVerticalScroller = shouldScroll;
    if (hadScroll != shouldScroll) {
      [_scrollView tile];
      [self scheduleMeasure];
      return;
    }
  } else {
    BOOL hadScroll = _scrollView.hasVerticalScroller;
    _scrollView.hasVerticalScroller = NO;
    if (hadScroll) {
      [_scrollView tile];
      [self scheduleMeasure];
      return;
    }
  }

  if (self.onContentHeightChange) {
    self.onContentHeightChange(0, height, (NSInteger)_textView.string.length);
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

  _hasUserEdited = YES;

  if (self.onChangeText) {
    self.onChangeText(_textView.string ?: @"");
  }
}

- (void)handleApplicationDidBecomeActive:(NSNotification *)notification
{
  if (_suppressesSpellPanelsAfterActivation) {
    [self closeSharedSpellPanelsIfNeeded];
  }
}

- (void)handleApplicationWillResignActive:(NSNotification *)notification
{
  BOOL ourTextViewIsActiveResponder =
      self.window != nil &&
      (self.window.firstResponder == _textView || self.window.firstResponder == self);
  BOOL hasVisibleManagedPanels = [self hasVisibleManagedSpellPanels];
  if (ourTextViewIsActiveResponder || hasVisibleManagedPanels) {
    _suppressesSpellPanelsAfterActivation = YES;
    if (ourTextViewIsActiveResponder) {
      [self.window makeFirstResponder:nil];
    }
    [self closeSharedSpellPanelsIfNeeded];
  } else {
    _suppressesSpellPanelsAfterActivation = NO;
  }
}

- (void)handleWindowDidBecomeKey:(NSNotification *)notification
{
  NSWindow *window = (NSWindow *)notification.object;
  if (_suppressesSpellPanelsAfterActivation && [self isManagedSpellPanelWindow:window]) {
    [self closeSharedSpellPanelsIfNeeded];
  }
}

- (BOOL)textView:(NSTextView *)textView
    shouldChangeTextInRange:(NSRange)__unused affectedCharRange
          replacementString:(NSString *)replacementString
{
  if (textView != _textView) {
    return YES;
  }
  if (replacementString.length >= 32) {
    [self scheduleMeasure];
  }
  return YES;
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
    if (!shift) {
      if (self.onSubmitText) {
        self.onSubmitText(_textView.string ?: @"");
      }
      return YES;
    }
  }

  return NO;
}

@end

@interface CLCMacTextView : RCTViewComponentView <RCTCLCMacTextViewViewProtocol>
@end

@implementation CLCMacTextView {
  CLCMacTextViewContentView *_macTextViewContentView;
}

+ (ComponentDescriptorProvider)componentDescriptorProvider
{
  return concreteComponentDescriptorProvider<CLCMacTextViewComponentDescriptor>();
}

- (instancetype)initWithFrame:(CGRect)frame
{
  if ((self = [super initWithFrame:frame])) {
    static const auto defaultProps = std::make_shared<const CLCMacTextViewProps>();
    _props = defaultProps;

    _macTextViewContentView = [[CLCMacTextViewContentView alloc] initWithFrame:self.bounds];
    __weak __typeof(self) weakSelf = self;
    _macTextViewContentView.onChangeText = ^(NSString *text) {
      __typeof(self) strongSelf = weakSelf;
      if (!strongSelf || !strongSelf->_eventEmitter) {
        return;
      }
      auto const &eventEmitter =
          *std::static_pointer_cast<CLCMacTextViewEventEmitter const>(strongSelf->_eventEmitter);
      eventEmitter.onChange({.text = std::string(text.UTF8String ?: "")});
    };
    _macTextViewContentView.onSubmitText = ^(NSString *text) {
      __typeof(self) strongSelf = weakSelf;
      if (!strongSelf || !strongSelf->_eventEmitter) {
        return;
      }
      auto const &eventEmitter =
          *std::static_pointer_cast<CLCMacTextViewEventEmitter const>(strongSelf->_eventEmitter);
      eventEmitter.onSubmit({.text = std::string(text.UTF8String ?: "")});
    };
    _macTextViewContentView.onContentHeightChange = ^(CGFloat width, CGFloat height, NSInteger textLength) {
      __typeof(self) strongSelf = weakSelf;
      if (!strongSelf || !strongSelf->_eventEmitter) {
        return;
      }
      auto const &eventEmitter =
          *std::static_pointer_cast<CLCMacTextViewEventEmitter const>(strongSelf->_eventEmitter);
      eventEmitter.onMacContentSizeChange(
          {.width = width, .height = height, .textLength = static_cast<int>(textLength)});
    };
    self.contentView = _macTextViewContentView;
  }

  return self;
}

- (void)prepareForRecycle
{
  [_macTextViewContentView resetForRecycle];
  [super prepareForRecycle];
}

- (void)updateProps:(const Props::Shared &)props oldProps:(const Props::Shared &)oldProps
{
  const auto &newProps = static_cast<const CLCMacTextViewProps &>(*props);

  _macTextViewContentView.initialText = RCTNSStringFromString(newProps.initialText);
  _macTextViewContentView.placeholder = RCTNSStringFromString(newProps.placeholder);
  _macTextViewContentView.editable = newProps.editable;
  _macTextViewContentView.autoGrow = newProps.autoGrow;
  _macTextViewContentView.maxHeight = newProps.maxHeight;
  _macTextViewContentView.textColor = RCTUIColorFromSharedColor(newProps.textColor);
  _macTextViewContentView.placeholderTextColor =
      RCTUIColorFromSharedColor(newProps.placeholderTextColor);
  _macTextViewContentView.fontSize = newProps.fontSize;

  [super updateProps:props oldProps:oldProps];
}

- (void)handleCommand:(const NSString *)commandName args:(const NSArray *)args
{
  RCTCLCMacTextViewHandleCommand(self, commandName, args);
}

- (void)setText:(NSString *)text
{
  [_macTextViewContentView setTextProgrammatically:text];
}

- (void)focus
{
  [_macTextViewContentView focusInput];
}

@end

Class<RCTComponentViewProtocol> CLCMacTextViewCls(void)
{
  return CLCMacTextView.class;
}

#endif