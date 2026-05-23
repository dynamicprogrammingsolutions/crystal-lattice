import React, { useEffect, useRef } from 'react';
import {
  StyleSheet,
  View,
  Animated,
  Text,
  useColorScheme,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { AppLogo } from './AppLogo';

export const AnimatedSplashScreen: React.FC = () => {
  const scheme = useColorScheme();
  const isDark = scheme === 'dark';

  // Premium design palettes from the brand specifications
  const splashBg = isDark ? '#0b172d' : '#e9ecf4';
  const splashText = isDark ? '#FFFFFF' : '#0b162c';
  const splashSubtext = isDark ? '#00E5FF' : '#0091FF';

  // Animation values
  const floatAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // 1. Initial fade-in of the content
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 850,
      useNativeDriver: true,
    }).start();

    // 2. Infinite floating / bounce loop
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: -18,
          duration: 1600,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1600,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [fadeAnim, floatAnim]);

  // Interpolations for the floating logo
  const logoTranslateY = floatAnim;

  return (
    <View style={[styles.container, { backgroundColor: splashBg }]}>
      <StatusBar
        barStyle={isDark ? 'light-content' : 'dark-content'}
        backgroundColor={splashBg}
        translucent
      />

      <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
        {/* Floating App Logo Container */}
        <Animated.View
          style={[
            styles.logoContainer,
            {
              transform: [{ translateY: logoTranslateY }],
            },
          ]}
        >
          <AppLogo type="square" width={108} height={108} />
        </Animated.View>

        {/* Branding & Status Info */}
        <View style={styles.textContainer}>
          <Text style={[styles.brandTitle, { color: splashText }]}>
            Crystal Lattice
          </Text>
          <Text style={[styles.brandSubtitle, { color: splashSubtext }]}>
            AI CODE ENGINE
          </Text>

          <View style={styles.spinnerContainer}>
            <ActivityIndicator size="small" color={splashSubtext} />
          </View>
        </View>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
    position: 'relative',
    width: 240,
    height: 120,
  },
  textContainer: {
    marginTop: 48,
    alignItems: 'center',
  },
  brandTitle: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: 0.2,
    textAlign: 'center',
    fontFamily: 'System',
  },
  brandSubtitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 3,
    marginTop: 8,
    textAlign: 'center',
  },
  spinnerContainer: {
    marginTop: 56,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
