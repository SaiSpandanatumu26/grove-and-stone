import { Asset } from 'expo-asset';
import { View, ViewStyle, StyleProp } from 'react-native';
import type { PhotoProps } from './Photo';
import { imageSource } from './imageSource';

export function Photo({ src, label, style }: PhotoProps) {
  const { source, placeholder } = imageSource(src);
  const uri = typeof source === 'number' ? Asset.fromModule(source).uri : source.uri;
  return <View style={[{ width: '100%', aspectRatio: 1, backgroundColor: '#FFFAF2', borderRadius: 14, overflow: 'hidden' }, style as StyleProp<ViewStyle>]}>
    <img src={uri} alt={label} loading="lazy" decoding="async" style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', backgroundImage: placeholder ? `url(${placeholder})` : undefined, backgroundSize: 'cover' }} />
  </View>;
}
