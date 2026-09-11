import { useEffect, useMemo, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, PanResponder, Platform, Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { FruitVideo } from './FruitVideo';
import { Category } from './api';
import { useShop } from './Store';
import { Button, colors, Icon, s, useWide } from './ui';

const collections: { key: Category; title: string; note: string; icon: 'sunny-outline' | 'leaf-outline' | 'nutrition-outline' }[] = [
  { key: 'mango', title: 'Mango moments', note: 'Explore the season', icon: 'sunny-outline' },
  { key: 'exotic', title: 'A taste of adventure', note: 'Discover exotic fruits', icon: 'leaf-outline' },
  { key: 'dry_fruit', title: 'Your daily handful', note: 'Shop dry fruits', icon: 'nutrition-outline' },
];

export function Hero({ choose, mangoSeason }: { choose: (category: Category | 'all') => void; mangoSeason: () => void }) {
  const { banners, products } = useShop(), wide = useWide(), focused = useIsFocused();
  const [index, setIndex] = useState(0), [manual, setManual] = useState(false), [reduced, setReduced] = useState(true), [active, setActive] = useState(AppState.currentState === 'active');
  const reveal = useRef(new Animated.Value(1)).current;
  const slide = banners.length ? index % banners.length : 0, banner = banners[slide];
  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then(value => { if (mounted) setReduced(value); });
    const motion = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced), app = AppState.addEventListener('change', state => setActive(state === 'active'));
    return () => { mounted = false; motion.remove(); app.remove(); };
  }, []);
  useEffect(() => {
    if (manual || reduced || !focused || !active || banners.length < 2) return;
    const timer = setTimeout(() => setIndex(value => (value + 1) % banners.length), 6500);
    return () => clearTimeout(timer);
  }, [index, banners.length, manual, reduced, focused, active]);
  useEffect(() => {
    reveal.setValue(reduced ? 1 : 0);
    const animation = Animated.timing(reveal, { toValue: 1, duration: 450, useNativeDriver: Platform.OS !== 'web' });
    animation.start(); return () => animation.stop();
  }, [banner?.id, reduced]);
  const change = (next: number) => { setIndex((next + banners.length) % banners.length); setManual(true); };
  const swipe = useMemo(() => PanResponder.create({
    onMoveShouldSetPanResponderCapture: (_, gesture) => banners.length > 1 && Math.abs(gesture.dx) > 18 && Math.abs(gesture.dx) > Math.abs(gesture.dy) * 1.5,
    onPanResponderRelease: (_, gesture) => {
      if (Math.abs(gesture.dx) < 50 || Math.abs(gesture.dx) < Math.abs(gesture.dy) * 1.5) return;
      setIndex(value => (value + (gesture.dx < 0 ? 1 : -1) + banners.length) % banners.length); setManual(true);
    },
    onPanResponderTerminationRequest: () => true,
  }), [banners.length]);
  if (!banner) return null;
  const mango = banner.cta_url.includes('mango'), dry = banner.cta_url.includes('dry_fruit');
  const follow = () => mango ? mangoSeason() : choose(dry ? 'dry_fruit' : banner.cta_url.includes('exotic') ? 'exotic' : 'all');
  const count = products.filter(product => product.category === 'mango').length;
  return <><View {...swipe.panHandlers} style={[h.hero, Platform.OS === 'web' && ({ touchAction: 'pan-y' } as ViewStyle & { touchAction: 'pan-y' })]} accessibilityActions={[{ name: 'increment', label: 'Next offer' }, { name: 'decrement', label: 'Previous offer' }]} onAccessibilityAction={event => change(slide + (event.nativeEvent.actionName === 'increment' ? 1 : -1))}>
    <FruitVideo playing={!reduced && focused && active} />
    <View style={[h.inner, !wide && { flexDirection: 'column', padding: 18, paddingTop: 90, gap: 0 }]}>
      <Animated.View style={[h.copy, { width: wide ? '52%' : '100%', opacity: reveal, padding: wide ? 28 : 20, gap: wide ? 20 : 16, backgroundColor: wide ? '#FFF8E5EB' : '#FFF8E5B8' }]}>
        <View style={h.pill}><Icon name="leaf" size={14} color="#38512B" /><Text style={h.eyebrow}>SMALL JOYS. BIG FLAVOURS.</Text></View>
        <Text accessibilityRole="header" style={[h.title, !wide && { fontSize: 36, lineHeight: 40, letterSpacing: -1.2 }]}>{banner.title}</Text>
        <Text style={h.subtitle}>{banner.subtitle}</Text>
        <View style={[s.wrap, { marginTop: 8 }]}><Button label={banner.cta_label} icon="arrow-forward" onPress={follow} />
          <Pressable accessibilityRole="button" onPress={() => choose('all')} style={h.secondary}><Text style={h.secondaryText}>Browse all fruits</Text><Icon name="arrow-forward-outline" size={18} color={colors.dark} /></Pressable>
        </View>
        <View style={[s.wrap, { marginTop: 8, gap: 18 }]}><View style={s.row}><Icon name="basket-outline" size={18} color="#604617" /><Text style={h.detail}>Packs for every basket</Text></View><View style={s.row}><Icon name="location-outline" size={18} color="#604617" /><Text style={h.detail}>Know your fruit's origin</Text></View></View>
      </Animated.View>
      {wide && <View style={[h.art, { width: '44%', maxWidth: 470, height: 440 }]}>
        <View style={h.stamp}><Icon name={mango ? 'sunny' : 'sparkles'} size={23} color="#355429" /><Text style={h.stampText}>{mango ? 'MANGO\nMOMENTS' : 'A BASKET\nOF HAPPY'}</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel="Explore mango collection" onPress={mangoSeason} style={h.floatingCard}><View style={h.sun}><Icon name="sunny-outline" size={25} /></View><View style={{ flex: 1 }}><Text style={h.cardLabel}>THE MANGO EDIT</Text><Text style={h.cardTitle}>{count ? `${count} varieties to discover` : 'Explore the seasonal collection'}</Text></View><Icon name="arrow-forward" /></Pressable>
      </View>}
    </View>
    <View style={[h.controls, !wide && { paddingHorizontal: 22 }]}>
      <View style={[s.row, { gap: 3 }]}>{banners.map((item, i) => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Show slide ${i + 1}`} accessibilityState={{ selected: i === slide }} onPress={() => change(i)} style={h.dotTarget}><View style={[h.dot, i === slide && h.dotActive]} /></Pressable>)}</View>

    </View>
  </View>
    {wide && <View style={h.collectionBar}><View style={[h.collections, !wide && { flexDirection: 'column', padding: 12, gap: 0 }]}>{collections.map(item => <Pressable key={item.key} accessibilityRole="button" accessibilityLabel={item.note} onPress={() => item.key === 'mango' ? mangoSeason() : choose(item.key)} style={[h.collection, !wide && { width: '100%', paddingVertical: 12 }]}><View style={h.collectionIcon}><Icon name={item.icon} size={24} /></View><View style={{ flex: 1 }}><Text style={h.collectionTitle}>{item.title}</Text><Text style={h.collectionNote}>{item.note}</Text></View><Icon name="arrow-forward-outline" size={19} /></Pressable>)}</View></View>}
  </>;
}

const h = StyleSheet.create({
  hero: { backgroundColor: '#FFCC43', overflow: 'hidden' },
  inner: { maxWidth: 1230, width: '100%', alignSelf: 'center', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 38, paddingTop: 44, gap: 24 }, copy: { gap: 20, borderRadius: 26, backgroundColor: '#FFF8E5EB', boxShadow: '0 12px 40px #80500010' },
  pill: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#FFF6D6', borderRadius: 30, paddingHorizontal: 14, paddingVertical: 9 }, eyebrow: { fontSize: 10, fontWeight: '800', letterSpacing: 1.6, color: '#38512B' },
  title: { color: '#30291C', fontSize: 68, lineHeight: 72, fontWeight: '900', letterSpacing: -3 }, subtitle: { color: '#624D25', fontSize: 17, lineHeight: 27, maxWidth: 465 },
  secondary: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 4 }, secondaryText: { color: colors.dark, fontWeight: '700', fontSize: 14 }, detail: { fontSize: 12, color: '#604617' },
  art: { padding: 18, paddingBottom: 35, marginTop: 12 },
  stamp: { position: 'absolute', right: 0, top: 8, width: 92, height: 92, backgroundColor: '#E9F0C9', borderRadius: 46, alignItems: 'center', justifyContent: 'center', gap: 5, transform: [{ rotate: '12deg' }], borderWidth: 4, borderColor: '#FFF8DA' }, stampText: { color: '#355429', fontSize: 10, fontWeight: '900', textAlign: 'center', letterSpacing: 1 },
  floatingCard: { position: 'absolute', bottom: 9, left: 0, right: 14, flexDirection: 'row', alignItems: 'center', gap: 12, padding: 15, borderRadius: 16, backgroundColor: '#FFFEF8', boxShadow: '0 12px 30px #80500020' }, sun: { backgroundColor: '#FFF0C4', borderRadius: 12, padding: 10 }, cardLabel: { color: colors.orange, fontWeight: '800', fontSize: 9, letterSpacing: 1.5 }, cardTitle: { color: colors.dark, fontWeight: '800', fontSize: 14, marginTop: 4 },
  controls: { maxWidth: 1230, width: '100%', alignSelf: 'center', paddingHorizontal: 38, paddingBottom: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }, dotTarget: { width: 28, height: 48, justifyContent: 'center' }, dot: { width: 7, height: 7, borderRadius: 8, backgroundColor: '#88651B60' }, dotActive: { width: 24, backgroundColor: '#453215' },
  collectionBar: { backgroundColor: '#FFF9EB', borderBottomWidth: 1, borderColor: '#F0E8DD' }, collections: { maxWidth: 1230, width: '100%', alignSelf: 'center', flexDirection: 'row', paddingHorizontal: 24, gap: 20 }, collection: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 13, padding: 20 }, collectionIcon: { padding: 10, backgroundColor: '#FFF0D4', borderRadius: 14 }, collectionTitle: { color: colors.dark, fontWeight: '800', fontSize: 15 }, collectionNote: { color: colors.muted, fontSize: 12, marginTop: 4 },
});
