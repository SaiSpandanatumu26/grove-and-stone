import { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { useIsFocused, useNavigation } from '@react-navigation/native';
import { all, api, Cart, Customer, Order } from './api';
import { ProductGrid } from './Home';
import { useShop } from './Store';
import { Button, colors, Copy, dateLabel, Empty, Eyebrow, Field, Heading, Icon, money, Page, s, useWide } from './ui';

function LoginForm({ next }: { next?: string }) {
  const navigation = useNavigation<any>();
  const shop = useShop(), [signup, setSignup] = useState(false), [name, setName] = useState(''), [email, setEmail] = useState(''), [phone, setPhone] = useState(''), [password, setPassword] = useState('');
  const submit = async () => { const success = await shop.perform(async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) throw new Error('Enter a valid email address.');
    if (!password || signup && password.length < 8) throw new Error('Use at least 8 characters for your password.');
    if (signup && (name.trim().length < 2 || name.trim().length > 80)) throw new Error('Enter a name between 2 and 80 characters.');
    if (signup && !/^[0-9]{10}$/.test(phone)) throw new Error('Enter a 10-digit mobile number.');
    await shop.authenticate({ email: email.trim(), password, ...(signup ? { full_name: name.trim(), phone } : {}) }, signup);
    setPassword('');
  }); if (success && next === 'Checkout') { navigation.setParams({ next: undefined }); navigation.getParent()?.navigate('Cart', { screen: 'Checkout' }); } };
  return <View style={[s.panel, { flex: 1, width: '100%', maxWidth: 490 }]}>
    <Eyebrow>YOUR CORNER OF THE GROVE</Eyebrow><Heading>{signup ? 'Create your account' : 'Welcome back.'}</Heading><Copy>{signup ? 'A few details, and you’re ready to explore.' : 'Log in to save your favourites and pick up where you left off.'}</Copy>
    {signup && <Field label="Full name" value={name} onChangeText={setName} maxLength={80} autoComplete="name" />}
    <Field label="Email address" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" maxLength={320} />
    {signup && <Field label="Mobile number" placeholder="10-digit mobile number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" maxLength={10} autoComplete="tel" />}
    <Field label="Password" placeholder={signup ? 'At least 8 characters' : 'Your password'} value={password} onChangeText={setPassword} secureTextEntry autoCapitalize="none" autoComplete={signup ? 'new-password' : 'current-password'} onSubmitEditing={submit} />
    <Button label={shop.busy ? 'Please wait…' : signup ? 'Create account' : 'Log in'} onPress={submit} disabled={shop.busy} icon="arrow-forward" />
    <Button label={signup ? 'Already a member? Log in' : 'New here? Create account'} quiet disabled={shop.busy} onPress={() => { setSignup(!signup); shop.setNotice(''); setPassword(''); }} />
  </View>;
}

function Profile() {
  const shop = useShop(), [name, setName] = useState(shop.customer!.full_name), [phone, setPhone] = useState(shop.customer!.phone);
  return <View style={[s.panel, { maxWidth: 620 }]}><Heading>Your details</Heading>
    <Field label="Full name" value={name} onChangeText={setName} maxLength={80} /><Field label="Email address" value={shop.customer!.email} editable={false} />
    <Field label="Mobile number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" maxLength={10} />
    <Button label="Save details" disabled={shop.busy} onPress={() => shop.perform(async () => {
      if (name.trim().length < 2 || !/^[0-9]{10}$/.test(phone)) throw new Error('Enter your name and a valid 10-digit mobile number.');
      shop.setCustomer(await api<Customer>('/me', 'PATCH', { full_name: name.trim(), phone }));
    }, 'Your details have been saved.')} />
  </View>;
}

function Orders({ reorderOnly }: { reorderOnly: boolean }) {
  const shop = useShop(), navigation = useNavigation<any>(), [orders, setOrders] = useState<Order[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const focused = useIsFocused();
  const load = () => { setLoading(true); setError(''); all<Order>('/orders').then(setOrders).catch(error => setError(error.message)).finally(() => setLoading(false)); };
  useEffect(() => { if (focused) load(); }, [shop.customer?.id, focused]);
  if (loading) return <Copy>Loading your orders…</Copy>;
  if (error) return <View style={{ gap: 16 }}><Copy>{error}</Copy><Button label="Try again" onPress={load} /></View>;
  if (!orders.length) return <Empty icon={reorderOnly ? 'repeat-outline' : 'receipt-outline'} title={reorderOnly ? 'Favourites worth repeating' : 'You have no orders yet'} body={reorderOnly ? 'Your previous orders will appear here, ready to add to your cart again.' : 'Your order history will be right here after your first purchase.'}><Button label="Explore the shop" onPress={() => navigation.getParent()?.navigate('Home')} /></Empty>;
  return <View style={{ gap: 20 }}><Copy>{reorderOnly ? 'Add a previous order to your cart at today’s prices. We check stock before adding anything.' : 'Your previous orders, all in one place.'}</Copy>
    {orders.map(order => <View key={order.id} style={s.panel}>
      <View style={[s.between, { flexWrap: 'wrap' }]}><View style={{ gap: 6 }}><Text style={[s.label, { fontSize: 19 }]}>{order.order_number}</Text><Copy>{dateLabel(order.created_at)}</Copy></View><Text style={s.badge}>{order.status.replaceAll('_', ' ')}</Text><Text style={[s.label, { fontSize: 22 }]}>{money(order.grand_total)}</Text></View>
      <View style={s.wrap}>{!reorderOnly && <Button label={'View ' + order.order_number} quiet disabled={shop.busy} onPress={() => navigation.navigate('Order', { number: order.order_number })} />}
        <Button label={'Reorder ' + order.order_number} icon="repeat-outline" disabled={shop.busy} onPress={async () => {
          if (await shop.perform(async () => shop.setCart(await api<Cart>('/orders/' + order.order_number + '/reorder', 'POST', {})), 'Items added to your cart at current prices.')) navigation.getParent()?.navigate('Cart', { screen: 'Landing' });
        }} /></View>
    </View>)}
  </View>;
}

export function AccountScreen({ route }: any) {
  const shop = useShop(), wide = useWide(), [section, setSection] = useState('Profile');
  useEffect(() => { if (route.params?.section) setSection(route.params.section); }, [route.params?.section]);
  if (!shop.customer) return <Page><View style={[s.row, { flexDirection: wide ? 'row' : 'column', alignItems: 'center', gap: 55, paddingVertical: 24 }]}>
    <View style={{ flex: 1, gap: 24, width: '100%' }}><Eyebrow>GOOD TASTE. GREAT COMPANY.</Eyebrow><Text accessibilityRole="header" style={{ fontSize: wide ? 49 : 34, fontWeight: '900', letterSpacing: -1.5, color: colors.dark }}>Make yourself{wide ? '\n' : ' '}at home.</Text><Copy>A fresh little space for everything you love.</Copy>
      {[['heart-outline', 'Your wishlist', 'Save something delicious for another day.'], ['receipt-outline', 'Your orders', 'Find every previous order in one place.'], ['repeat-outline', 'One-tap reorder', 'Put your favourites back in your basket.']].map(([icon, title, body]) => <View key={title} style={s.row}><View style={s.emptyIcon}><Icon name={icon as any} size={25} /></View><View style={{ flex: 1 }}><Text style={s.label}>{title}</Text><Copy>{body}</Copy></View></View>)}
    </View><LoginForm next={route.params?.next} />
  </View></Page>;
  return <Page><View style={[s.between, { flexWrap: 'wrap' }]}><View style={{ gap: 9 }}><Eyebrow>YOUR ACCOUNT</Eyebrow><Heading>Hello, {shop.customer.full_name.split(' ')[0]}.</Heading><Copy>A little space for all your favourites.</Copy></View><Button label="Log out" quiet icon="log-out-outline" disabled={shop.busy} onPress={() => shop.perform(shop.logout, 'You have been logged out.')} /></View>
    <View style={s.wrap}>{['Profile', 'Wishlist', 'Orders', 'Reorder'].map(item => <Button key={item} label={item === 'Wishlist' ? `Wishlist (${shop.wishlist.length})` : item} quiet={item !== section} onPress={() => setSection(item)} />)}</View>
    {section === 'Profile' && <Profile key={shop.customer.id} />}
    {section === 'Wishlist' && (shop.wishlist.length ? <ProductGrid products={shop.wishlist} /> : <Empty icon="heart-outline" title="Save a little something" body="Tap the heart on any product to add it to your wishlist." />)}
    {(section === 'Orders' || section === 'Reorder') && <Orders reorderOnly={section === 'Reorder'} />}
  </Page>;
}
