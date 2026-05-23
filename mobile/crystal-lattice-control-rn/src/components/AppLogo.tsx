import React from 'react';
import { View, useColorScheme, ViewStyle, StyleProp } from 'react-native';
import { SvgXml } from 'react-native-svg';
import * as SvgAssets from '../assets/icons/SvgAssets';

interface AppLogoProps {
  type?: 'square' | 'full';
  themeOverride?: 'light' | 'dark';
  width?: number | string;
  height?: number | string;
  style?: StyleProp<ViewStyle>;
}

export const AppLogo: React.FC<AppLogoProps> = ({
  type = 'square',
  themeOverride,
  width,
  height,
  style,
}) => {
  const systemScheme = useColorScheme();
  const isDark = themeOverride ? themeOverride === 'dark' : systemScheme === 'dark';

  let xml = '';
  if (type === 'square') {
    xml = isDark ? SvgAssets.ICON_DARK : SvgAssets.ICON_LIGHT;
  } else {
    xml = isDark ? SvgAssets.ICON_FULL_DARK : SvgAssets.ICON_FULL_LIGHT;
  }

  // default aspect ratios:
  // square is 638 x 630 (~1:1)
  // full is 2160 x 630 (~3.4:1)
  let defaultWidth: number | string = 120;
  let defaultHeight: number | string = 120;

  if (type === 'full') {
    defaultWidth = 240;
    defaultHeight = 70;
  }

  return (
    <View style={style}>
      <SvgXml
        xml={xml}
        width={width ?? defaultWidth}
        height={height ?? defaultHeight}
      />
    </View>
  );
};
