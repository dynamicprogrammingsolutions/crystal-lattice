import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Dimensions,
  Modal,
  StyleSheet,
  TouchableWithoutFeedback,
  View,
  type LayoutRectangle,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

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
  if (!visible) {
    return null;
  }

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <TouchableWithoutFeedback onPress={onRequestClose}>
        <View style={[styles.modalBackdrop, backdropStyle]}>
          <TouchableWithoutFeedback onPress={() => {}}>
            <View style={[styles.modalContent, contentStyle]}>{children}</View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
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
  const [anchorLayout, setAnchorLayout] = useState<LayoutRectangle | null>(null);
  const [menuLayout, setMenuLayout] = useState<LayoutRectangle | null>(null);

  const measureAnchor = useCallback(() => {
    const current = anchorRef.current;
    if (!current || typeof current.measureInWindow !== 'function') {
      setAnchorLayout(null);
      return;
    }
    current.measureInWindow((x: number, y: number, width: number, height: number) => {
      setAnchorLayout({ x, y, width, height });
    });
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
    if (!anchorLayout) {
      return null;
    }

    const window = Dimensions.get('window');
    const offsetX = offset?.x ?? 0;
    const offsetY = offset?.y ?? 0;

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
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <TouchableWithoutFeedback onPress={onRequestClose}>
        <View style={[styles.modalBackdrop, backdropStyle]}>
          <TouchableWithoutFeedback
            onPress={() => {
              // Stop propagation.
            }}
          >
            {position ? (
              <View
                style={[styles.dropdownMenu, { left: position.left, top: position.top }, menuStyle]}
                onLayout={(event) => {
                  setMenuLayout(event.nativeEvent.layout);
                }}
              >
                {children}
              </View>
            ) : (
              <View
                style={[styles.dropdownMenu, styles.dropdownMenuHidden, menuStyle]}
                onLayout={(event) => {
                  setMenuLayout(event.nativeEvent.layout);
                }}
              >
                {children}
              </View>
            )}
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingVertical: 8,
  },
  dropdownMenu: {
    position: 'absolute',
    minWidth: 200,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingVertical: 6,
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
