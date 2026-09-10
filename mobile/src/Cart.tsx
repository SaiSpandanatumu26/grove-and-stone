import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { api } from './api';
import { useShop } from './Store';
import { StockStatus } from './StockStatus';
import { Button, colors, Copy, Empty, Eyebrow, Field, Heading, IconButton, money, Page, Photo, s, useWide } from './ui';

export function PincodeScreen() {
  const shop = useShop(), [pincode, setPincode] = useState(shop.cart?.pincode || ''), [result, setResult] = useState('');
  const check = () => shop.perform(async () => {
    if (!/^[0-9]{6}$/.test(pincode)) throw new Error('Enter a valid 6-digit pincode.');
    const value = await api('/cart/pincode', 'PUT', { pincode }); shop.setCart(value.cart);
    const area = value.pincode_service;
    setResult(area.serviceable ? `${area.city} · ${area.delivery_days_min}–${area.delivery_days_max} days. ${area.mango_eligible ? 'Fresh fruits and dry fruits can be delivered here.' : 'Dry fruit delivery available. Fresh fruit delivery is unavailable here.'}` : 'We don’t deliver to this pincode yet. Try another delivery location.');
  });
  return <Page><View style={[s.panel, { maxWidth: 620 }]}><Eyebrow>LET’S FIND YOUR NEIGHBOURHOOD</Eyebrow><Heading>Where shall we deliver?</Heading><Copy>Check availability before filling your basket.</Copy><Field label="Delivery pincode" placeholder="6-digit pincode" value={pincode} onChangeText={value => { setPincode(value); setResult(''); }} keyboardType="number-pad" maxLength={6} onSubmitEditing={check} /><Button label="Check availability" icon="location-outline" disabled={shop.busy} onPress={check} />{!!result && <Text accessibilityLiveRegion="polite" style={s.copy}>{result}</Text>}</View></Page>;
}

export function CartScreen() {
  const shop = useShop(), navigation = useNavigation<any>(), wide = useWide(), [confirmClear, setConfirmClear] = useState(false), cart = shop.cart;
  if (!cart?.lines.length) return <Page><Empty icon="bag-handle-outline" title="Your cart is empty" body="There’s a whole grove of good things waiting for you."><Button label="Find your favourites" icon="arrow-forward" onPress={() => navigation.getParent()?.navigate('Home')} /></Empty></Page>;
  const change = (id: string, qty?: number) => shop.perform(async () => { await api('/cart/lines/' + id, qty ? 'PATCH' : 'DELETE', qty ? { qty } : undefined); await shop.refreshCart(); });
  return <Page><View style={s.between}><View style={{ gap: 8 }}><Eyebrow>GOOD CHOICES, ALL TOGETHER</Eyebrow><Heading>Your basket</Heading><Copy>{cart.lines.reduce((total, line) => total + line.qty, 0)} {cart.lines.reduce((total, line) => total + line.qty, 0) === 1 ? 'pack' : 'packs'} of goodness</Copy></View><Button label="Clear cart" quiet disabled={shop.busy} onPress={() => setConfirmClear(true)} /></View><StockStatus />
    {confirmClear && <View style={s.panel}><Copy>Remove all items from your cart?</Copy><View style={s.wrap}><Button label="Yes, clear cart" disabled={shop.busy} onPress={() => shop.perform(async () => { await api('/cart/lines', 'DELETE'); await shop.refreshCart(); setConfirmClear(false); })} /><Button label="Keep items" quiet onPress={() => setConfirmClear(false)} /></View></View>}
    <View style={[s.row, { flexDirection: wide ? 'row' : 'column', alignItems: 'flex-start', gap: 28 }]}>
      <View style={{ flex: 1, width: '100%', gap: 14 }}>{cart.lines.map(line => <View key={line.id} style={[s.panel, { padding: 18 }]}><View style={[s.row, { alignItems: 'flex-start' }]}>
        <Photo src={line.product.images[0]} label={line.product.name} style={{ width: wide ? 115 : 82, height: wide ? 115 : 82 }} />
        <View style={{ flex: 1, gap: 8 }}><Pressable accessibilityRole="button" onPress={() => navigation.navigate('Product', { slug: line.product.slug })}><Text style={[s.label, { fontSize: 18 }]}>{line.product.name}</Text></Pressable><Copy>{line.variant.pack_label} · {money(line.unit_price)}</Copy>
          <Copy>{line.product.is_active === false || ['off_season', 'coming_soon'].includes(line.product.season_status) ? 'No longer available. Remove this item to continue.' : line.variant.stock_qty === 0 ? 'Sold out. Remove this item to continue.' : line.qty > line.variant.stock_qty ? `Only ${line.variant.stock_qty} packs left. Reduce your quantity to continue.` : `${line.variant.stock_qty} packs available`}</Copy>
          <View style={[s.between, { flexWrap: 'wrap' }]}><View style={[s.row, { gap: 3, borderWidth: 1, borderColor: colors.line, borderRadius: 10 }]}><IconButton label={'Decrease ' + line.product.name} icon="remove" disabled={shop.busy || line.qty <= 1 || line.variant.stock_qty === 0 || line.product.is_active === false || ['off_season', 'coming_soon'].includes(line.product.season_status)} onPress={() => change(line.id, Math.min(line.qty - 1, line.variant.stock_qty))} /><Text accessibilityLabel={'Quantity ' + line.qty} style={s.label}>{line.qty}</Text><IconButton label={'Increase ' + line.product.name} icon="add" disabled={shop.busy || line.qty >= Math.min(20, line.variant.stock_qty) || line.product.is_active === false || ['off_season', 'coming_soon'].includes(line.product.season_status)} onPress={() => change(line.id, line.qty + 1)} /></View><Text style={[s.label, { fontSize: 19 }]}>{money(line.line_total)}</Text></View>
        </View><IconButton label={'Remove ' + line.product.name} icon="trash-outline" disabled={shop.busy} onPress={() => change(line.id)} />
      </View></View>)}<Button label="Continue shopping" quiet icon="arrow-back" onPress={() => navigation.getParent()?.navigate('Home')} /></View>
      <View style={[s.panel, { width: wide ? 345 : '100%', backgroundColor: colors.cream }]}><Heading>Order summary</Heading>
        <View style={s.between}><Copy>Subtotal</Copy><Text style={s.label}>{money(cart.subtotal)}</Text></View>
        <View style={s.between}><Copy>Included GST</Copy><Text style={s.label}>{money(cart.included_gst)}</Text></View>
        <View style={s.between}><Copy>Delivery</Copy><Text style={s.label}>At checkout</Text></View><View style={s.divider} />
        <View style={s.between}><Text style={[s.label, { fontSize: 18 }]}>Total before delivery</Text><Text style={[s.label, { fontSize: 21 }]}>{money(cart.total_before_shipping)}</Text></View>
        <Copy>Prices include GST. Delivery charges will be confirmed at checkout.</Copy><Button label={cart.pincode ? 'Delivery to ' + cart.pincode : 'Check delivery pincode'} quiet icon="location-outline" onPress={() => navigation.navigate('Pincode')} />
        {!!cart.block_reason && !['LOGIN_REQUIRED', 'PINCODE_REQUIRED'].includes(cart.block_reason) && <Copy>{({ PINCODE_NOT_SERVICEABLE: 'This pincode is not serviceable.', MANGO_NOT_ELIGIBLE: 'Fresh fruit delivery is not available for this pincode.', PRODUCT_UNAVAILABLE: 'An item is no longer available. Remove it to continue.', INSUFFICIENT_STOCK: 'A pack has insufficient stock. Reduce its quantity or remove it.' } as Record<string, string>)[cart.block_reason] || cart.block_reason}</Copy>}
        {!shop.customer && <Button label="Log in to check out" icon="person-outline" onPress={() => navigation.getParent()?.navigate('Account', { screen: 'Landing', params: { next: 'Checkout' } })} />}
        {shop.stockIssue && <Copy>Stock has changed. Update the items above before checking out.</Copy>}
        {!!shop.customer && <Button label="Continue to checkout" icon="arrow-forward" onPress={() => navigation.navigate('Checkout')} disabled={shop.busy || shop.stockIssue} />}
      </View>
    </View>
  </Page>;
}
