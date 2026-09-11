import { useEffect, useState } from 'react';
import { Image, StyleSheet, View } from 'react-native';
import { useEvent } from 'expo';
import { useVideoPlayer, VideoView } from 'expo-video';

export function FruitVideo({ playing }: { playing: boolean }) {
  const [ready, setReady] = useState(false);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const width = Math.max(size.width, size.height * 16 / 9);
  const frame = { position: 'absolute' as const, top: 0, height: size.height, width, right: size.width < 820 ? -(width - size.width) * .12 : -(width - size.width) / 2 };
  const player = useVideoPlayer(require('../assets/hero/grove-and-stone-fruit-loop.mp4'), video => { video.loop = true; video.muted = true; });
  const { status } = useEvent(player, 'statusChange', { status: player.status });
  useEffect(() => { if (playing) player.play(); else player.pause(); }, [player, playing]);
  return <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" onLayout={({ nativeEvent }) => setSize(nativeEvent.layout)} style={[StyleSheet.absoluteFill, { overflow: 'hidden' }]}>
    <VideoView player={player} nativeControls={false} playsInline contentFit="cover" surfaceType="textureView" onFirstFrameRender={() => setReady(true)} style={frame} />
    {(!ready || status === 'error') && <Image source={require('../assets/hero/fruit-loop-poster.jpg')} resizeMode="cover" style={frame} />}
  </View>;
}
