import { PointerEvent, ReactNode, useRef } from 'react';

export function SwipeArea({ children, onSwipe }: { children: ReactNode; onSwipe: (direction: number) => void }) {
  const start = useRef<{ x: number; y: number; id: number } | null>(null), swiped = useRef(false);
  const horizontal = (event: PointerEvent<HTMLDivElement>, distance: number) => start.current && Math.abs(event.clientX - start.current.x) >= distance && Math.abs(event.clientX - start.current.x) > Math.abs(event.clientY - start.current.y) * 1.5;
  return <div style={{ touchAction: 'pan-y', userSelect: 'none' }} onPointerDown={event => {
    if (!event.isPrimary || event.button !== 0) return;
    start.current = { x: event.clientX, y: event.clientY, id: event.pointerId }; swiped.current = false;
  }} onPointerMove={event => {
    if (start.current?.id === event.pointerId && horizontal(event, 18)) event.currentTarget.setPointerCapture(event.pointerId);
  }} onPointerUp={event => {
    if (start.current?.id === event.pointerId && horizontal(event, 50)) {
      swiped.current = true; onSwipe(event.clientX < start.current.x ? 1 : -1);
    }
    start.current = null;
  }} onPointerCancel={() => { start.current = null; }} onClickCapture={event => {
    if (swiped.current) { event.preventDefault(); event.stopPropagation(); swiped.current = false; }
  }}>{children}</div>;
}
