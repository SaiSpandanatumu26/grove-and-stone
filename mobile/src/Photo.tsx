import { Image } from 'expo-image';
import { ImageStyle, StyleProp } from 'react-native';
import { imageSource } from './imageSource';

export type PhotoProps = { src: string; label: string; style?: StyleProp<ImageStyle> };
export function Photo({ src, label, style }: PhotoProps) {
  const { source, placeholder } = imageSource(src);
  return <Image source={source} placeholder={placeholder} accessibilityLabel={label} accessible contentFit="cover" placeholderContentFit="cover" cachePolicy="memory-disk" recyclingKey={src} transition={150}
    style={[{ width: '100%', aspectRatio: 1, backgroundColor: '#FFFAF2', borderRadius: 14 }, style]} />;
}
