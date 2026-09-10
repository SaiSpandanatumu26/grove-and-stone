import { useEffect, useState } from 'react';
import { Linking, Text, View } from 'react-native';
import { useIsFocused, useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';
import { api, Cart, Order } from './api';
import { useShop } from './Store';
import { StockStatus } from './StockStatus';
import { Button, Copy, dateLabel, Empty, Eyebrow, Field, Heading, money, Page, s, useWide } from './ui';

type Address = { id?: string; full_name: string; phone: string; line1: string; line2: string; city: string; state: string; pincode: string; landmark: string; address_type: string };
const addressFields = (value: Address): Address => Object.fromEntries(['id', 'full_name', 'phone', 'line1', 'line2', 'city', 'state', 'pincode', 'landmark', 'address_type'].map(key => [key, value[key as keyof Address]])) as Address;
type Quote = { quote_id: string; cart: Cart & { cod_allowed: boolean }; shipping: string; grand_total: string; delivery_dates: string[]; states: string[]; payment_backend: string; area: { city: string; state: string; delivery_days_min: number; delivery_days_max: number } };

export function CheckoutScreen() {
  const shop = useShop(), navigation = useNavigation<any>(), wide = useWide(), key = 'gs-checkout-' + shop.customer?.id;
  const [address, setAddress] = useState<Address>({ full_name: shop.customer?.full_name || '', phone: shop.customer?.phone || '', line1: '', line2: '', city: '', state: '', pincode: shop.cart?.pincode || '', landmark: '', address_type: 'home' });
  const [saved, setSaved] = useState<Address[]>([]), [quote, setQuote] = useState<Quote | null>(null), [day, setDay] = useState(''), [method, setMethod] = useState('upi'), [notes, setNotes] = useState(''), [showStates, setShowStates] = useState(false), [ready, setReady] = useState(false);
  const openOrder = async (order: Order) => { await shop.refreshCart(); await AsyncStorage.removeItem(key); navigation.replace('Order', { number: order.order_number }); };
  useEffect(() => { if (!shop.customer) { setReady(true); return; } shop.perform(async () => {
    const attempt = await AsyncStorage.getItem(key);
    if (attempt) { const result = await api('/checkout/attempts/' + attempt); if (result.order) { await openOrder(result.order); return; } }
    setSaved((await api('/me/addresses')).items.map(addressFields));
    setReady(true);
  }); }, [shop.customer?.id]);
  const update = (field: keyof Address, value: string) => { setAddress({ ...address, id: undefined, [field]: value }); if (field === 'pincode') setQuote(null); };
  const getQuote = () => shop.perform(async () => {
    setQuote(null);
    const result = await api<Quote>('/checkout/quote', 'POST', { pincode: address.pincode });
    setQuote(result); shop.setCart(result.cart); setDay(result.delivery_dates[0]);
    setAddress(current => ({ ...current, city: current.city || result.area.city, state: current.state || result.area.state }));
    if (!result.cart.cod_allowed && method === 'cod') setMethod('upi');
    if (result.payment_backend === 'disabled' && result.cart.cod_allowed) setMethod('cod');
  });
  const place = () => shop.perform(async () => {
    if (!quote) throw new Error('Check delivery and review your total first.');
    const requestId = await AsyncStorage.getItem(key) || Crypto.randomUUID();
    await AsyncStorage.setItem(key, requestId);
    const previous = await api('/checkout/attempts/' + requestId);
    if (previous.order) { await openOrder(previous.order); return; }
    const { id, ...fields } = address;
    const result = await api('/checkout', 'POST', { request_id: requestId, quote_id: quote.quote_id, ...(id ? { address_id: id } : { address: fields }), delivery_date: day, payment_method: method, customer_notes: notes });
    await openOrder(result.order);
  });
  if (!shop.customer) return <Page><Empty icon="person-outline" title="Log in to check out" body="Your basket will be here when you return."><Button label="Log in" onPress={() => navigation.getParent()?.navigate('Account', { screen: 'Landing', params: { next: 'Checkout' } })} /></Empty></Page>;
  if (!ready) return <Page><Copy>Checking your saved checkout…</Copy><Button label="Try again" disabled={shop.busy} onPress={() => navigation.replace('Checkout')} /></Page>;
  if (!shop.cart?.lines.length) return <Page><Empty icon="bag-handle-outline" title="Your basket is empty" body="Add a few favourites before checking out."><Button label="Back to shop" onPress={() => navigation.getParent()?.navigate('Home')} /></Empty></Page>;
  return <Page><Eyebrow>THE LAST LITTLE STEP</Eyebrow><Heading>Fresh finds, headed your way.</Heading><View style={[s.row, { alignItems: 'flex-start', flexDirection: wide ? 'row' : 'column', gap: 28 }]}>
    <View style={[s.panel, { flex: 1, width: '100%' }]}><Heading>Delivery address</Heading>
      {!!saved.length && <View style={{ gap: 10 }}><Copy>Your saved addresses</Copy>{saved.map(item => <Button key={item.id} label={`${item.full_name} · ${item.line1} · ${item.pincode}`} quiet={address.id !== item.id} onPress={() => { setAddress(item); setQuote(null); }} />)}<Button label="Use a new address" quiet onPress={() => { setAddress({ ...address, id: undefined, line1: '', line2: '', landmark: '' }); setQuote(null); }} /></View>}
      <Field label="Full name" value={address.full_name} onChangeText={value => update('full_name', value)} maxLength={80} />
      <Field label="Mobile number" value={address.phone} onChangeText={value => update('phone', value)} keyboardType="phone-pad" maxLength={10} />
      <Field label="Address line 1" placeholder="House, building and street" value={address.line1} onChangeText={value => update('line1', value)} maxLength={120} />
      <Field label="Address line 2 (optional)" value={address.line2 || ''} onChangeText={value => update('line2', value)} maxLength={120} />
      <Field label="Delivery pincode" value={address.pincode} onChangeText={value => update('pincode', value)} keyboardType="number-pad" maxLength={6} />
      <Button label="Check delivery & total" icon="location-outline" onPress={getQuote} disabled={shop.busy} />
      <Field label="City" value={address.city} onChangeText={value => update('city', value)} maxLength={80} />
      <Button label={address.state || 'Choose state / union territory'} quiet onPress={() => setShowStates(!showStates)} />
      {showStates && (quote ? <View style={s.wrap}>{quote.states.map(state => <Button key={state} label={state} quiet={state !== address.state} onPress={() => { update('state', state); setShowStates(false); }} />)}</View> : <Copy>Check your delivery pincode to load the state list.</Copy>)}
      <Field label="Landmark (optional)" value={address.landmark || ''} onChangeText={value => update('landmark', value)} maxLength={80} />
      <View style={s.wrap}>{['home', 'office', 'other'].map(type => <Button key={type} label={type[0].toUpperCase() + type.slice(1)} quiet={address.address_type !== type} onPress={() => update('address_type', type)} />)}</View>
      <Button label="Save address to account" quiet disabled={shop.busy || !!address.id || !quote} onPress={() => shop.perform(async () => {
        const { id, ...fields } = address;
        const result = addressFields(await api('/me/addresses', 'POST', { ...fields, is_default: saved.length === 0 })); setSaved([...saved, result]); setAddress(result);
      }, 'Address saved.')} />
      {quote && <><Heading>Delivery day</Heading><Copy>{quote.area.city} · Usually {quote.area.delivery_days_min}–{quote.area.delivery_days_max} days</Copy><View style={s.wrap}>{quote.delivery_dates.map(value => <Button key={value} label={dateLabel(value)} quiet={day !== value} onPress={() => setDay(value)} />)}</View>
        <Field label="Delivery notes (optional)" value={notes} onChangeText={setNotes} multiline maxLength={200} /><Heading>How would you like to pay?</Heading>
        <View style={s.wrap}>{(quote.payment_backend === 'disabled' ? [] : ['upi', 'card']).concat(quote.cart.cod_allowed ? ['cod'] : []).map(value => <Button key={value} label={value === 'cod' ? 'Cash on delivery' : value.toUpperCase()} quiet={method !== value} onPress={() => setMethod(value)} />)}</View>
        {quote.payment_backend === 'demo' && method !== 'cod' && <Copy>Local demo payment. You can simulate success or failure on the next screen. No money is charged.</Copy>}
        <StockStatus />{shop.stockIssue && <><Copy>Stock has changed. Return to your cart and update unavailable quantities.</Copy><Button label="Review cart" quiet onPress={() => navigation.navigate('Landing')} /></>}
        <Button label={shop.busy ? 'Please wait…' : method === 'cod' ? 'Place order · ' + money(quote.grand_total) : 'Continue to payment · ' + money(quote.grand_total)} onPress={place} disabled={shop.busy || shop.stockIssue || quote.payment_backend === 'disabled' && !quote.cart.cod_allowed} />
        <Button label="Refresh total" quiet onPress={getQuote} disabled={shop.busy} />
      </>}
    </View><View style={[s.panel, { width: wide ? 340 : '100%' }]}><Heading>Your order</Heading>{(quote?.cart || shop.cart).lines.map(line => <View key={line.id} style={s.between}><View style={{ flex: 1 }}><Text style={s.label}>{line.product.name}</Text><Copy>{line.variant.pack_label} × {line.qty}</Copy></View><Text style={s.label}>{money(line.line_total)}</Text></View>)}<View style={s.divider} />
      <Summary subtotal={(quote?.cart || shop.cart).subtotal} gst={(quote?.cart || shop.cart).included_gst} shipping={quote?.shipping} total={quote?.grand_total} />
    </View></View></Page>;
}

export function Summary({ subtotal, gst, shipping, total }: { subtotal: string; gst: string; shipping?: string; total?: string }) {
  return <>{[['Subtotal', money(subtotal)], ['Included GST', money(gst)], ['Delivery', shipping === undefined ? 'Check pincode' : money(shipping)], ['Total', total === undefined ? 'Check pincode' : money(total)]].map(([label, value]) => <View key={label} style={s.between}><Copy>{label}</Copy><Text style={s.label}>{value}</Text></View>)}<Copy>GST is included in the prices above.</Copy></>;
}

export function OrderScreen({ route }: any) {
  const shop = useShop(), navigation = useNavigation<any>(), focused = useIsFocused(), [order, setOrder] = useState<Order | null>(null), [error, setError] = useState(''), [confirm, setConfirm] = useState(false);
  const load = () => api<Order>('/orders/' + route.params.number).then(value => { setOrder(value); setError(''); }).catch(error => setError(error.message));
  useEffect(() => { if (focused) load(); }, [route.params.number, focused]);
  useEffect(() => { if (!focused || order?.status !== 'pending_payment') return; const timer = setInterval(load, 6000); return () => clearInterval(timer); }, [focused, order?.status]);
  const demo = (outcome: string) => shop.perform(async () => setOrder(await api('/orders/' + order!.order_number + '/demo-payment', 'POST', { outcome })));
  if (!order) return <Page><Copy>{error || 'Loading your order…'}</Copy><Button label="Try again" onPress={load} /></Page>;
  const expired = !!order.payment_expires_at && Date.parse(order.payment_expires_at) <= Date.now(), steps = ['confirmed', 'packed', 'shipped', 'delivered'];
  return <Page><Eyebrow>{order.status === 'pending_payment' ? 'ONE MORE STEP' : order.status === 'cancelled' ? 'ORDER CANCELLED' : 'THANK YOU FOR SHOPPING WITH US'}</Eyebrow><Heading>{order.status === 'pending_payment' ? 'Complete your payment' : order.status === 'cancelled' ? 'Your order has been cancelled' : 'Your order is ' + order.status}</Heading><Copy>{order.order_number}</Copy>
    {!!error && <Copy>{error}</Copy>}
    <View style={s.panel}><View style={s.wrap}>{steps.map((step, index) => <Text key={step} style={[s.badge, { opacity: order.status !== 'cancelled' && steps.indexOf(order.status) >= index ? 1 : 0.4 }]}>{index + 1}. {step[0].toUpperCase() + step.slice(1)}</Text>)}</View>
      <Copy>Delivery date: {dateLabel(order.delivery_date)}</Copy><Copy>Payment: {order.payment_method.toUpperCase()} · {order.payment_status}</Copy>
      {order.status === 'pending_payment' && <>{expired ? <Copy>The payment window has expired. Start a new cart or contact support.</Copy> : <><Copy>{order.payment_status === 'failed' ? 'Payment failed. Try again.' : 'Your items are reserved for 30 minutes while you pay.'}</Copy>
        {order.payment_backend === 'demo' ? <><Copy>LOCAL PAYMENT SIMULATOR · No real charge.</Copy><View style={s.wrap}><Button label="Simulate successful payment" disabled={shop.busy} onPress={() => demo('success')} /><Button label="Simulate failed payment" quiet disabled={shop.busy} onPress={() => demo('failure')} /></View></> : <Button label="Open secure payment" disabled={shop.busy} onPress={() => shop.perform(async () => { const session = await api('/orders/' + order.order_number + '/payment-session', 'POST', {}); await Linking.openURL(session.url); })} />}</>}</>}
      {!!order.refund && <Copy>Refund: {order.refund.status === 'processed' ? 'Processed' : 'Requested; awaiting processing'} · {money(order.refund.amount)}{order.payment_backend === 'demo' ? ' (local demo)' : ''}</Copy>}
      <Button label="Refresh order status" quiet onPress={load} />
      {order.status === 'confirmed' && <Button label="Cancel order" quiet onPress={() => setConfirm(true)} />}
      {confirm && order.status === 'confirmed' && <View style={{ gap: 12 }}><Copy>Cancel this order? Paid online orders will be queued for a refund.</Copy><View style={s.wrap}><Button label="Yes, cancel order" disabled={shop.busy} onPress={() => shop.perform(async () => { setOrder(await api('/orders/' + order.order_number + '/cancel', 'POST', {})); setConfirm(false); })} /><Button label="Keep order" quiet onPress={() => setConfirm(false)} /></View></View>}
    </View><View style={s.panel}><Heading>Order details</Heading>{order.lines?.map((line, index) => <View key={index} style={s.between}><Copy>{line.product_name} · {line.variant_label} × {line.qty}</Copy><Text style={s.label}>{money(line.line_total)}</Text></View>)}<View style={s.divider} /><Summary subtotal={order.subtotal} gst={order.gst} shipping={order.shipping} total={order.grand_total} /></View>
    <View style={s.panel}><Heading>Deliver to</Heading><Copy>{order.address.full_name} · {order.address.phone}</Copy><Copy>{[order.address.line1, order.address.line2, order.address.city, order.address.state, order.address.pincode, order.address.landmark].filter(Boolean).join(', ')}</Copy>{!!order.customer_notes && <Copy>{order.customer_notes}</Copy>}</View>
    <View style={s.wrap}><Button label="Continue shopping" onPress={() => navigation.getParent()?.navigate('Home', { screen: 'Landing' })} /><Button label="My orders" quiet onPress={() => navigation.getParent()?.navigate('Account', { screen: 'Landing', params: { section: 'Orders' } })} /></View>
  </Page>;
}
