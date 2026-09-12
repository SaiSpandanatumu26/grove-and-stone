import { ReactNode, useMemo } from 'react';
import { PanResponder, View } from 'react-native';

export type SwipeProps = { children: ReactNode; onSwipe: (direction: number) => void };
export function SwipeArea({ children, onSwipe }: SwipeProps) {
  const gesture = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponderCapture: (_, g) => Math.abs(g.dx) > 18 && Math.abs(g.dx) > Math.abs(g.dy) * 1.5,
    onPanResponderRelease: (_, g) => { if (Math.abs(g.dx) >= 50 && Math.abs(g.dx) > Math.abs(g.dy) * 1.5) onSwipe(g.dx < 0 ? 1 : -1); },
    onPanResponderTerminationRequest: () => true,
  }), [onSwipe]);
  return <View {...gesture.panHandlers}>{children}</View>;
}
