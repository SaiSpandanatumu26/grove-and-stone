import { useEffect, useRef, useState } from 'react';
import { Animated, Platform, StyleSheet, View } from 'react-native';
import { useEvent } from 'expo';
import { useVideoPlayer, VideoView } from 'expo-video';

export function FruitVideo({ playing }: { playing: boolean }) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const width = Math.max(size.width, size.height * 16 / 9);
  const frame = { position: 'absolute' as const, top: 0, height: size.height, width, right: size.width < 820 ? -(width - size.width) * .12 : -(width - size.width) / 2 };
  const player = useVideoPlayer(require('../assets/hero/grove-and-stone-fruit-loop.mp4'), video => { video.loop = true; video.muted = true; });
  const { status } = useEvent(player, 'statusChange', { status: player.status });
  const { isPlaying } = useEvent(player, 'playingChange', { isPlaying: player.playing });
  const drift = useRef(new Animated.Value(0)).current;
  const covered = status !== 'readyToPlay' || !isPlaying;
  useEffect(() => { if (playing) player.play(); else player.pause(); }, [player, playing]);
  useEffect(() => {
    if (Platform.OS !== 'web' || !playing) return;
    const resume = () => player.play();
    document.addEventListener('touchstart', resume, { passive: true });
    document.addEventListener('pointerdown', resume, { passive: true });
    return () => { document.removeEventListener('touchstart', resume); document.removeEventListener('pointerdown', resume); };
  }, [player, playing]);
  useEffect(() => {
    if (!playing || !covered) { drift.setValue(0); return; }
    const motion = Animated.loop(Animated.sequence([
      Animated.timing(drift, { toValue: 1, duration: 3500, useNativeDriver: Platform.OS !== 'web' }),
      Animated.timing(drift, { toValue: 0, duration: 3500, useNativeDriver: Platform.OS !== 'web' }),
    ]));
    motion.start(); return () => motion.stop();
  }, [playing, covered, drift]);
  return <View pointerEvents="none" accessible={false} importantForAccessibility="no-hide-descendants" onLayout={({ nativeEvent }) => setSize(nativeEvent.layout)} style={[StyleSheet.absoluteFill, { overflow: 'hidden' }]}>
    <VideoView player={player} nativeControls={false} playsInline contentFit="cover" surfaceType="textureView" style={frame} />
    {covered && <Animated.Image source={require('../assets/hero/fruit-loop-poster.jpg')} resizeMode="cover" style={[frame, { transform: [{ scale: 1.12 }, { translateX: drift.interpolate({ inputRange: [0, 1], outputRange: [-12, 12] }) }, { translateY: drift.interpolate({ inputRange: [0, 1], outputRange: [8, -8] }) }] }]} />}
  </View>;
}
