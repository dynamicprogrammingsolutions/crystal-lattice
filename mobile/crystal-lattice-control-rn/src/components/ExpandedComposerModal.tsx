import React, { useEffect, useMemo, useRef } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  AttachmentThumbnailStrip,
  type AttachmentLike,
} from './AttachmentThumbnailStrip';
import { useTheme, type Theme } from '../theme';

export interface ExpandedComposerModalProps {
  visible: boolean;
  value: string;
  onChangeText: (value: string) => void;
  onCollapse: () => void;
  onSend: () => Promise<boolean>;
  canSend: boolean;
  sending: boolean;
  attachmentsAbove: AttachmentLike[];
  attachmentsBelow: AttachmentLike[];
  onOpenAttachmentsAbove: () => void;
  onOpenAttachmentsBelow: () => void;
  attachmentsDisabled: boolean;
}

export default function ExpandedComposerModal(
  props: ExpandedComposerModalProps
): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const inputRef = useRef<TextInput | null>(null);

  useEffect(() => {
    if (!props.visible) {
      return;
    }
    const timer = setTimeout(() => inputRef.current?.focus(), 80);
    return () => clearTimeout(timer);
  }, [props.visible]);

  const handleSend = async () => {
    const accepted = await props.onSend();
    if (accepted) {
      props.onCollapse();
    }
  };

  return (
    <Modal
      visible={props.visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={props.onCollapse}
    >
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          style={styles.root}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View style={styles.header}>
            <TouchableOpacity
              testID="expanded-composer-collapse"
              accessibilityRole="button"
              accessibilityLabel="Collapse composer"
              style={styles.headerButton}
              hitSlop={8}
              onPressIn={Platform.OS === 'ios' ? props.onCollapse : undefined}
              onPress={props.onCollapse}
            >
              <Icon name="minimize-2" size={20} color={theme.primary} />
            </TouchableOpacity>
            <Text style={styles.title}>Compose message</Text>
            <TouchableOpacity
              testID="expanded-composer-send"
              accessibilityRole="button"
              accessibilityLabel="Send message"
              style={[
                styles.headerButton,
                !props.canSend && styles.disabledButton,
              ]}
              disabled={!props.canSend}
              onPress={() => {
                void handleSend();
              }}
            >
              {props.sending ? (
                <ActivityIndicator size="small" color={theme.primary} />
              ) : (
                <Icon name="send" size={20} color={theme.primary} />
              )}
            </TouchableOpacity>
          </View>

          <AttachmentThumbnailStrip
            attachments={props.attachmentsAbove}
            onPressManageAll={props.onOpenAttachmentsAbove}
            disabled={props.attachmentsDisabled}
          />

          <TextInput
            ref={inputRef}
            testID="expanded-composer-input"
            accessibilityLabel="Expanded message composer"
            style={styles.input}
            value={props.value}
            onChangeText={props.onChangeText}
            multiline
            textAlignVertical="top"
            autoCapitalize="sentences"
            autoCorrect
            placeholder="Type your message..."
            placeholderTextColor={theme.textSecondary}
          />

          <AttachmentThumbnailStrip
            attachments={props.attachmentsBelow}
            onPressManageAll={props.onOpenAttachmentsBelow}
            disabled={props.attachmentsDisabled}
          />
        </KeyboardAvoidingView>
      </SafeAreaView>
    </Modal>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    safeArea: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    root: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    header: {
      minHeight: 52,
      flexDirection: 'row',
      alignItems: 'center',
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
      paddingHorizontal: 8,
    },
    headerButton: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
    },
    disabledButton: {
      opacity: 0.45,
    },
    title: {
      flex: 1,
      textAlign: 'center',
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      color: theme.text,
    },
    input: {
      flex: 1,
      margin: 12,
      padding: 14,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
  });
