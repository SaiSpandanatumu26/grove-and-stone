import { infoPages } from './Info';
import { Hero } from './Hero';
import { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useIsFocused, useNavigation } from '@react-navigation/native';
import { api, all, Category, Product, Season, Variant } from './api';
import { useShop } from './Store';
import { StockStatus } from './StockStatus';
import { Button, colors, Copy, dateLabel, Empty, Eyebrow, Field, Heading, Icon, IconButton, money, Page, Photo, s, useWide } from './ui';

export const categories: { key: Category; label: string; caption: string }[] = [
  { key: 'exotic', label: 'Exotic fruits', caption: 'A world of fresh discoveries' },
  { key: 'dry_fruit', label: 'Dry fruits', caption: 'Goodness by the handful' },
  { key: 'mango', label: 'Mangoes', caption: 'The sweetest time of year' },
];
const useNav = () => useNavigation<any>();
const seasonFor = (seasons: Season[], id: string) => seasons.filter(season => season.product?.id === id).sort((a, b) => b.harvest_start.localeCompare(a.harvest_start))[0];
const acceptsWaitlist = (season?: Season) => !!season && (season.waitlist_enabled || season.status === 'upcoming');

export function ProductGrid({ products }: { products: Product[] }) {
  const shop = useShop(), navigation = useNav(), [gridWidth, setGridWidth] = useState(0);
  const columns = Math.min(4, Math.max(1, Math.floor((gridWidth + 16) / 176)));
  const focused = useIsFocused(), ids = products.map(product => product.id).sort().join(',');
  useEffect(() => { if (focused && ids) return shop.watchStock(ids.split(',')); }, [focused, ids, shop.watchStock]);
  return <View style={{ gap: 12 }}>{products.length > 0 && <StockStatus />}<View style={h.grid} onLayout={event => setGridWidth(event.nativeEvent.layout.width)}>{products.map(original => {
    const product = shop.liveProduct(original);
    const variant = product.default_variant, saved = shop.wishlist.some(item => item.id === product.id);
    const unavailable = !variant || !variant.stock_qty || product.is_active === false || ['coming_soon', 'off_season'].includes(product.season_status);
    const notify = unavailable && product.is_active !== false && acceptsWaitlist(seasonFor(shop.seasons, product.id));
    return <View key={product.id} style={[h.card, { width: gridWidth ? (gridWidth - 16 * (columns - 1)) / columns : '100%' }]}>
      <View>
        <Pressable accessibilityRole="button" accessibilityLabel={'View ' + product.name} onPress={() => navigation.navigate('Product', { slug: product.slug })}>
          <Photo src={product.images[0]} label={product.name} />
        </Pressable>
        <View style={h.heart}><IconButton label={(saved ? 'Remove ' : 'Save ') + product.name + (saved ? ' from wishlist' : ' to wishlist')} icon={saved ? 'heart' : 'heart-outline'} active={saved} disabled={shop.busy} onPress={() => {
          if (!shop.customer) { shop.setNotice('Log in to save your favourites.'); navigation.getParent()?.navigate('Account'); }
          else shop.perform(() => shop.toggleWishlist(product), saved ? 'Removed from wishlist.' : 'Saved to wishlist.');
        }} /></View>
      </View>
      <Pressable accessibilityRole="button" onPress={() => navigation.navigate('Product', { slug: product.slug })}><Text numberOfLines={2} style={[h.productTitle, h.cardTitle]}>{product.name}</Text></Pressable>
      <View style={[s.row, { gap: 4, minHeight: 32 }]}><Icon name="location-outline" size={15} /><Text numberOfLines={2} style={h.origin}>{product.origin}</Text></View>
      <View style={h.cardFooter}>
      <Text numberOfLines={1} style={[h.pack, { minHeight: 18 }]}>{variant?.pack_label || 'No packs available'}</Text>
      <Text style={h.price}>{variant ? money(variant.price) : 'Unavailable'}</Text>
      <Text style={[h.pack, { color: unavailable ? colors.muted : colors.green, minHeight: 32 }]}>{unavailable ? 'Unavailable now' : variant!.stock_qty <= 5 ? `Only ${variant!.stock_qty} packs left` : 'In stock'}</Text>
      <View style={{ minHeight: 30 }}>{product.season_status !== 'in_season' && <Text style={s.badge}>{product.season_status.replaceAll('_', ' ')}</Text>}</View>
      <Button label={notify ? 'Notify me' : unavailable ? 'Unavailable' : 'Add to cart'} icon={notify ? 'notifications-outline' : unavailable ? undefined : 'add'} disabled={(unavailable && !notify) || shop.busy} onPress={() => notify ? navigation.navigate('Waitlist', { slug: product.slug }) : shop.perform(() => shop.add(variant!.id), product.name + ' added to cart.')} />
      </View>
    </View>;
  })}</View></View>;
}

export function HomeScreen() {
  const shop = useShop(), navigation = useNav(), [category, setCategory] = useState<Category | 'all'>('all');
  const scroll = useRef<ScrollView>(null), catalogY = useRef(0), contentY = useRef(0), wide = useWide();
  const choose = (key: Category | 'all') => { setCategory(key); scroll.current?.scrollTo({ y: contentY.current + catalogY.current, animated: true }); };
  return <ScrollView ref={scroll} style={s.page} contentContainerStyle={{ paddingBottom: 36 }}>
    <Hero choose={choose} mangoSeason={() => navigation.getParent()?.navigate('Mangoes')} />
    <View style={h.content} onLayout={event => { contentY.current = event.nativeEvent.layout.y; }}>
      <View style={[s.between, { flexWrap: 'wrap', paddingVertical: 24 }]}>
        <View style={s.row}><Icon name="location" /><View><Text style={s.label}>Freshness starts with your location</Text><Copy>{shop.cart?.pincode ? 'Deliver to ' + shop.cart.pincode : 'Check delivery availability in your area.'}</Copy></View></View>
        <Button label="Check pincode" quiet icon="arrow-forward" onPress={() => navigation.navigate('Pincode')} />
      </View>
      <View style={s.divider} />
      <View style={{ gap: 8, marginTop: 38, marginBottom: 24 }}><Eyebrow>THREE WAYS TO FIND YOUR FAVOURITES</Eyebrow><Heading>Search by category</Heading></View>
      <View style={[s.row, { alignItems: 'stretch', gap: wide ? 24 : 10 }]}>{categories.map(item => {
        const image = shop.products.find(product => product.category === item.key)?.images[0];
        return <Pressable key={item.key} accessibilityRole="button" accessibilityLabel={'Browse ' + item.label} onPress={() => choose(item.key)} style={h.category}>
          {image ? <Photo src={image} label={item.label} style={{ width: wide ? 135 : 86, height: wide ? 135 : 86, borderRadius: 90 }} /> : <Icon name="leaf-outline" size={70} />}
          <Text style={[h.categoryTitle, !wide && { fontSize: 14 }]}>{item.label}</Text>{wide && <Copy>{item.caption}</Copy>}
        </Pressable>;
      })}</View>
      {!!shop.seasons.length && <View style={h.seasonStrip}><View style={s.row}><Icon name="sunny-outline" size={30} /><View style={{ flex: 1 }}><Text style={h.productTitle}>A season worth waiting for</Text><Copy>{shop.seasons[0].variety_name} · {shop.seasons[0].status} · {dateLabel(shop.seasons[0].harvest_start)} – {dateLabel(shop.seasons[0].harvest_end)}</Copy></View></View><Button label="Explore mango season" quiet onPress={() => navigation.getParent()?.navigate('Mangoes')} /></View>}
      <View onLayout={event => { catalogY.current = event.nativeEvent.layout.y; }} style={{ gap: 24, paddingTop: 34, paddingBottom: 44 }}>
        <View style={s.between}><View style={{ gap: 8 }}><Eyebrow>FILL YOUR BASKET WITH GOODNESS</Eyebrow><Heading>This week</Heading></View><IconButton label="Search products" icon="search-outline" onPress={() => navigation.navigate('Search')} /></View>
        <View style={s.wrap}>{[{ key: 'all', label: 'All products' }, ...categories].map(item => <Button key={item.key} label={item.label} quiet={category !== item.key} onPress={() => setCategory(item.key as Category | 'all')} />)}</View>
        <ProductGrid products={shop.products.filter(product => category === 'all' || product.category === category)} />
        {!shop.products.some(product => category === 'all' || product.category === category) && <Empty icon="leaf-outline" title="More goodness on its way" body="There are no products in this category right now." />}
      </View>
    </View>
    <View style={h.how}><View style={[s.container, { padding: 24 }]}><Text accessibilityRole="header" style={[s.heading, { textAlign: 'center', color: colors.orange }]}>How does it work?</Text>
      <View style={[s.wrap, { justifyContent: 'space-around', alignItems: 'flex-start' }]}>{[
        ['location-outline', 'Select location', 'Check your pincode for delivery availability.'], ['bag-handle-outline', 'Choose your favourites', 'Pick your fruits, dry fruits and the perfect pack.'], ['receipt-outline', 'Review your basket', 'See every item and the included GST clearly.'], ['leaf-outline', 'Enjoy the good stuff', 'Origin stories, seasonal picks and everyday goodness.'],
      ].map(([icon, title, body]) => <View key={title} style={{ alignItems: 'center', gap: 12, width: wide ? '21%' : '45%', paddingVertical: 20 }}><Icon name={icon as any} size={42} /><Text style={[s.label, { textAlign: 'center', fontSize: 17 }]}>{title}</Text><Text style={[s.copy, { textAlign: 'center' }]}>{body}</Text></View>)}</View>
    </View></View>
    <View style={h.footer}><View style={[s.container, { padding: 24 }]}><Text style={{ color: '#FFFFFF', fontSize: 24, fontWeight: '800' }}>grove<Text style={{ color: colors.yellow }}>&stone</Text></Text><Text style={{ color: '#CCC6BF', lineHeight: 24 }}>Exotic fruits. Dry fruits. Seasonal mangoes. A basket full of possibilities.</Text><View style={s.wrap}>{infoPages.map(page => <Button key={page} label={page} quiet onPress={() => navigation.navigate('Info', { page })} />)}</View><Text style={{ color: '#A8A199', fontSize: 12 }}>Project preview · Sample catalog and prices for review</Text></View></View>
  </ScrollView>;
}

export function MangoScreen() {
  const shop = useShop(), navigation = useNav();
  return <Page><Eyebrow>THE SEASONAL COLLECTION</Eyebrow><Heading>Mango season</Heading><Copy>Discover varieties, origins and harvest windows. Availability follows the season.</Copy>
    {shop.seasons.map(season => <View key={season.id} style={[s.panel, { backgroundColor: colors.cream }]}><Text style={s.badge}>{season.status}</Text><Heading>{season.variety_name}</Heading><Copy>{dateLabel(season.harvest_start)} – {dateLabel(season.harvest_end)}</Copy>{season.product && (season.status === 'live' || acceptsWaitlist(season)) && <Button label={(season.status === 'live' ? 'Shop ' : 'Notify me about ') + season.product.name} onPress={() => navigation.navigate(season.status === 'live' ? 'Product' : 'Waitlist', { slug: season.product!.slug })} />}</View>)}
    <ProductGrid products={shop.products.filter(product => product.category === 'mango')} />
    {!shop.products.some(product => product.category === 'mango') && <Empty icon="leaf-outline" title="Between harvests" body="Check back here for the next mango season." />}
  </Page>;
}

export function SearchScreen() {
  const shop = useShop(), [query, setQuery] = useState(''), [items, setItems] = useState<Product[] | null>(null);
  const search = () => shop.perform(async () => {
    if (!query.trim() || query.trim().length > 80) throw new Error('Enter a search between 1 and 80 characters.');
    setItems(await all<Product>('/search?q=' + encodeURIComponent(query.trim())));
  });
  return <Page><Heading>Find your next favourite</Heading><Field label="Search fruits, origin or variety" placeholder="Try Alphonso, kiwi, almonds…" value={query} onChangeText={setQuery} maxLength={80} returnKeyType="search" onSubmitEditing={search} />
    <Button label="Search" icon="search" onPress={search} disabled={shop.busy} />{items && <ProductGrid products={items} />}
    {items?.length === 0 && <Empty icon="search-outline" title="No matches yet" body="Try another fruit, origin or variety." />}
  </Page>;
}

export function ProductScreen({ route }: any) {
  const navigation = useNav();
  const shop = useShop(), [original, setProduct] = useState<Product | null>(null), [selected, setVariant] = useState<Variant | null>(null), [error, setError] = useState(''), wide = useWide(), focused = useIsFocused();
  const product = original ? shop.liveProduct(original) : null, variant = product?.variants?.find(pack => pack.id === selected?.id) || null;
  const load = () => { setError(''); api<Product>('/products/' + route.params.slug).then(item => { setProduct(item); setVariant(item.variants?.find(pack => pack.is_default) || null); }).catch(error => setError(error.message)); };
  useEffect(load, [route.params.slug]);
  useEffect(() => { if (focused && original) return shop.watchStock([original.id]); }, [focused, original?.id, shop.watchStock]);
  if (!product) return <Page><Copy>{error || 'Loading your fresh find…'}</Copy>{!!error && <Button label="Try again" onPress={load} />}</Page>;
  const unavailable = !variant?.stock_qty || product.is_active === false || ['off_season', 'coming_soon'].includes(product.season_status);
  const notify = unavailable && product.is_active !== false && acceptsWaitlist(seasonFor(shop.seasons, product.id));
  return <Page><View style={[s.row, { alignItems: 'flex-start', flexDirection: wide ? 'row' : 'column', gap: 36 }]}>
    <Photo src={product.images[0]} label={product.name} style={{ width: wide ? '46%' : '100%' }} />
    <View style={{ flex: 1, gap: 20, width: wide ? undefined : '100%' }}><Eyebrow>{categories.find(item => item.key === product.category)?.label}</Eyebrow><Heading>{product.name}</Heading><Copy>{product.origin} · {product.short_description}</Copy>
      <Text style={s.label}>Choose your pack</Text><View style={s.wrap}>{product.variants?.map(pack => <Button key={pack.id} quiet={variant?.id !== pack.id} label={pack.pack_label} onPress={() => setVariant(pack)} />)}</View>
      <Heading>{money(variant?.price)}</Heading><Copy>Inclusive of GST ({variant?.gst_percent}%). {unavailable ? 'This pack is currently unavailable.' : variant!.stock_qty + ' packs available.'}</Copy><StockStatus />
      <Button label={notify ? 'Notify me' : unavailable ? 'Currently unavailable' : 'Add to cart'} icon={notify ? 'notifications-outline' : 'bag-add-outline'} disabled={(unavailable && !notify) || shop.busy} onPress={() => notify ? navigation.navigate('Waitlist', { slug: product.slug }) : shop.perform(() => shop.add(variant!.id), product.name + ' added to cart.')} />
      <View style={s.divider} /><Copy>{product.long_description}</Copy>{!!product.ripeness_note && <Copy>{product.ripeness_note}</Copy>}{!!product.handling_notes && <Copy>{product.handling_notes}</Copy>}
    </View>
  </View></Page>;
}

export function WaitlistScreen({ route }: any) {
  const shop = useShop(), navigation = useNav(), [message, setMessage] = useState('');
  const [name, setName] = useState(shop.customer?.full_name || ''), [email, setEmail] = useState(shop.customer?.email || ''), [phone, setPhone] = useState(shop.customer?.phone || '');
  const original = shop.products.find(item => item.slug === route.params.slug), product = original && shop.liveProduct(original);
  const season = product && seasonFor(shop.seasons, product.id), focused = useIsFocused();
  useEffect(() => { if (focused && product) return shop.watchStock([product.id]); }, [focused, product?.id, shop.watchStock]);
  useEffect(() => { setMessage(''); }, [route.params.slug]);
  if (!product || product.is_active === false) return <Page><Heading>Variety unavailable</Heading><Copy>This variety is no longer available.</Copy></Page>;
  const submit = () => shop.perform(async () => {
    if (!email.trim() && !phone.trim()) throw new Error('Enter email or mobile.');
    if (name.trim() && name.trim().length < 2) throw new Error('Enter a name between 2 and 80 characters.');
    if (phone.trim() && !/^[0-9]{10}$/.test(phone.trim())) throw new Error('Enter a 10-digit mobile number.');
    const result = await api<{ message: string }>('/mango-season/waitlist', 'POST', { product_id: product.id, ...(name.trim() && { full_name: name.trim() }), ...(email.trim() && { email: email.trim() }), ...(phone.trim() && { phone: phone.trim() }) });
    setMessage(result.message);
  });
  return <Page><Eyebrow>FIRST TO KNOW</Eyebrow><Heading>{product.name}</Heading><Photo src={product.images[0]} label={product.name} style={{ maxWidth: 280 }} /><Copy>{product.origin}</Copy>
    {season && <Copy>{season.variety_name} · {dateLabel(season.harvest_start)} – {dateLabel(season.harvest_end)}</Copy>}
    {message ? <View accessibilityLiveRegion="polite"><Heading>{message}</Heading><Copy>Your interest is saved for this variety. This does not reserve stock.</Copy></View> : acceptsWaitlist(season) ? <View style={s.panel}><Copy>Leave your email or mobile to register interest in the next harvest. No deposit or payment.</Copy>
      <Field label="Full name (optional)" value={name} onChangeText={setName} maxLength={80} autoComplete="name" />
      <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" maxLength={254} />
      <Field label="Mobile number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" maxLength={10} autoComplete="tel" />
      <Button label={shop.busy ? 'Saving…' : 'Notify me'} icon="notifications-outline" disabled={shop.busy} onPress={submit} />
    </View> : <Copy>This variety is not accepting waitlist entries right now.</Copy>}
    {season?.status === 'live' && <Button label="Shop this variety" onPress={() => navigation.navigate('Product', { slug: product.slug })} />}
    <Button label="Mango season" quiet onPress={() => { navigation.popToTop(); navigation.getParent()?.navigate('Mangoes'); }} />
  </Page>;
}

const h = StyleSheet.create({
  content: { maxWidth: 1230, width: '100%', alignSelf: 'center', paddingHorizontal: 24 }, category: { flex: 1, gap: 12, alignItems: 'center', backgroundColor: '#FFFCF7', borderRadius: 15, paddingVertical: 22 }, categoryTitle: { fontSize: 19, color: colors.dark, fontWeight: '800' },
  seasonStrip: { marginTop: 28, backgroundColor: '#FFF3DA', borderRadius: 13, padding: 22, gap: 15 }, grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, alignItems: 'stretch' }, card: { gap: 9, paddingBottom: 16 }, cardTitle: { minHeight: 48, lineHeight: 24 }, cardFooter: { marginTop: 'auto', gap: 9 },
  heart: { position: 'absolute', right: 8, top: 8, backgroundColor: '#FFFFFFE6', borderRadius: 12 }, productTitle: { color: colors.dark, fontSize: 18, fontWeight: '800', marginTop: 5 }, origin: { color: '#B05B15', fontSize: 12, flexShrink: 1 }, pack: { color: colors.muted, fontSize: 12 }, price: { color: colors.dark, fontSize: 20, fontWeight: '800', marginVertical: 3 },
  how: { backgroundColor: '#FFF8E9', paddingVertical: 24 }, footer: { backgroundColor: '#262320', paddingVertical: 24 },
});
