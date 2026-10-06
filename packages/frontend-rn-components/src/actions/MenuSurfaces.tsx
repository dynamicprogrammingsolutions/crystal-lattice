import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Dimensions,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  View,
  type LayoutRectangle,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { useTheme } from '../theme';
import { safeMeasureInWindow } from './safeMeasureInWindow';

export interface MenuSurfaceBaseProps {
  visible: boolean;
  onRequestClose: () => void;
  children: React.ReactNode;
  backdropStyle?: StyleProp<ViewStyle>;
  contentStyle?: StyleProp<ViewStyle>;
}

export const ModalMenuSurface: React.FC<MenuSurfaceBaseProps> = ({
  visible,
  onRequestClose,
  children,
  backdropStyle,
  contentStyle,
}) => {
  const theme = useTheme();
  const modalTransparent = Platform.OS !== 'macos';

  if (!visible) {
    return null;
  }

  return (
    <Modal
      visible
      transparent={modalTransparent}
      backdropColor={modalTransparent ? undefined : 'transparent'}
      animationType={Platform.OS === 'macos' ? 'none' : 'fade'}
      onRequestClose={onRequestClose}
    >
      <View
        style={[
          styles.backdropBase,
          { backgroundColor: theme.modalBackdrop },
          backdropStyle,
        ]}
      >
        <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
        <View
          style={[
            styles.modalContentBase,
            { backgroundColor: theme.surface },
            contentStyle,
          ]}
        >
          {children}
        </View>
      </View>
    </Modal>
  );
};

export interface DropdownMenuSurfaceProps extends Omit<MenuSurfaceBaseProps, 'contentStyle'> {
  anchorRef: React.RefObject<any>;
  offset?: { x?: number; y?: number };
  menuStyle?: StyleProp<ViewStyle>;
}

export const DropdownMenuSurface: React.FC<DropdownMenuSurfaceProps> = ({
  visible,
  onRequestClose,
  children,
  anchorRef,
  offset,
  backdropStyle,
  menuStyle,
}) => {
  const theme = useTheme();
  const modalTransparent = Platform.OS !== 'macos';
  const [anchorLayout, setAnchorLayout] = useState<LayoutRectangle | null>(null);
  const [menuLayout, setMenuLayout] = useState<LayoutRectangle | null>(null);

  const measureAnchor = useCallback(() => {
    const current = anchorRef.current;
    const ok = safeMeasureInWindow(current, (layout) => setAnchorLayout(layout));
    if (!ok) {
      setAnchorLayout(null);
    }
  }, [anchorRef]);

  useEffect(() => {
    if (!visible) {
      setAnchorLayout(null);
      setMenuLayout(null);
      return;
    }
    measureAnchor();
  }, [visible, measureAnchor]);

  const position = useMemo(() => {
    const window = Dimensions.get('window');
    const offsetX = offset?.x ?? 0;
    const offsetY = offset?.y ?? 0;

    if (!anchorLayout) {
      if (!menuLayout) {
        return null;
      }
      const left = Math.max(0, (window.width - menuLayout.width) / 2);
      const top = Math.max(0, (window.height - menuLayout.height) / 2);
      return { left, top };
    }

    let left = anchorLayout.x + offsetX;
    let top = anchorLayout.y + anchorLayout.height + offsetY;

    if (menuLayout) {
      const maxLeft = Math.max(0, window.width - menuLayout.width);
      left = Math.max(0, Math.min(left, maxLeft));

      const belowTop = anchorLayout.y + anchorLayout.height + offsetY;
      const aboveTop = anchorLayout.y - menuLayout.height - offsetY;
      const fitsBelow = belowTop + menuLayout.height <= window.height;
      const fitsAbove = aboveTop >= 0;
      top = fitsBelow ? belowTop : fitsAbove ? aboveTop : belowTop;

      const maxTop = Math.max(0, window.height - menuLayout.height);
      top = Math.max(0, Math.min(top, maxTop));
    }

    return { left, top };
  }, [anchorLayout, menuLayout, offset?.x, offset?.y]);

  if (!visible) {
    return null;
  }

  return (
    <Modal
      visible
      transparent={modalTransparent}
      backdropColor={modalTransparent ? undefined : 'transparent'}
      animationType={Platform.OS === 'macos' ? 'none' : 'fade'}
      onRequestClose={onRequestClose}
    >
      <View
        style={[
          styles.backdropBase,
          { backgroundColor: theme.modalBackdrop },
          backdropStyle,
        ]}
      >
        <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
        {position ? (
          <View
            style={[
              styles.dropdownMenuBase,
              { backgroundColor: theme.surface, borderColor: theme.border },
              { left: position.left, top: position.top },
              menuStyle,
            ]}
            onLayout={(event) => {
              setMenuLayout(event.nativeEvent.layout);
            }}
          >
            {children}
          </View>
        ) : (
          <View
            style={[
              styles.dropdownMenuBase,
              { backgroundColor: theme.surface, borderColor: theme.border },
              styles.dropdownMenuHidden,
              menuStyle,
            ]}
            onLayout={(event) => {
              setMenuLayout(event.nativeEvent.layout);
            }}
          >
            {children}
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdropBase: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContentBase: {
    width: '80%',
    maxHeight: '90%',
    borderRadius: 12,
    paddingVertical: 8,
  },
  dropdownMenuBase: {
    position: 'absolute',
    minWidth: 200,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 12,
    paddingVertical: 8,
    shadowColor: '#000',
    shadowOpacity: 0.18,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  dropdownMenuHidden: {
    left: 0,
    top: 0,
    opacity: 0,
  },
});
