import React from 'react';
import { View, useColorScheme, ViewStyle, StyleProp } from 'react-native';
import { SvgXml } from 'react-native-svg';
import * as SvgAssets from '../assets/icons/SvgAssets';

interface AppLogoProps {
  themeOverride?: 'light' | 'dark';
  width?: number | string;
  height?: number | string;
  style?: StyleProp<ViewStyle>;
}

export const AppLogo: React.FC<AppLogoProps> = ({
  themeOverride,
  width,
  height,
  style,
}) => {
  const systemScheme = useColorScheme();
  const isDark = themeOverride ? themeOverride === 'dark' : systemScheme === 'dark';
  const xml = isDark ? SvgAssets.ICON_DARK : SvgAssets.ICON_LIGHT;

  return (
    <View style={style}>
      <SvgXml
        xml={xml}
        width={width ?? 120}
        height={height ?? 120}
      />
    </View>
  );
};
