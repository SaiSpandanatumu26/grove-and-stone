import { useEffect, useState } from 'react';
import { Platform, Text, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from './api';
import { useShop } from './Store';
import { Button, Copy, Field, Heading, Page, Photo, s } from './ui';

const cards = [
  { title: 'Welcome to Grove & Stone', body: 'Explore exotic fruits and dry fruits. Choose a pack that suits your basket.', image: 'avocado' },
  { title: 'Make room for mango season', body: 'Discover varieties, origins and harvest windows, and join a seasonal waitlist.', image: 'mango' },
  { title: 'Freshness starts with your location', body: 'Add your delivery pincode, or check it later from Deliver to.', image: 'strawberries' },
];
export function Onboarding({ children }: { children: React.ReactNode }) {
  const shop = useShop(), [done, setDone] = useState(Platform.OS === 'web'), [loaded, setLoaded] = useState(Platform.OS === 'web');
  const [page, setPage] = useState(0), [pincode, setPincode] = useState(''), [saving, setSaving] = useState(false);
  useEffect(() => { if (Platform.OS !== 'web') AsyncStorage.getItem('gs-onboarding-done').then(value => setDone(value === 'true')).catch(() => {}).finally(() => setLoaded(true)); }, []);
  const finish = async (savePincode = false) => {
    setSaving(true);
    if (savePincode && pincode) {
      if (!/^[0-9]{6}$/.test(pincode)) shop.setNotice('Enter a valid 6-digit pincode from Deliver to when you are ready.');
      else if (!shop.ready || shop.failed) shop.setNotice('Check your delivery pincode from Deliver to after connecting.');
      else try { const result = await api('/cart/pincode', 'PUT', { pincode }, true, 5000); shop.setCart(result.cart); }
        catch { shop.setNotice('Your pincode could not be saved. Check it from Deliver to when connected.'); }
    }
    await AsyncStorage.setItem('gs-onboarding-done', 'true').catch(() => {});
    setDone(true); setSaving(false);
  };
  if (done) return <>{children}</>;
  if (!loaded) return <View style={s.empty}><Heading>Grove & Stone</Heading></View>;
  const card = cards[page];
  return <Page><View style={{ alignItems: 'flex-end' }}><Button quiet label="Skip" onPress={() => finish()} disabled={saving} /></View>
    <Photo src={'/api/v1/media/' + card.image + '.png'} label={card.title} style={{ maxWidth: 300, alignSelf: 'center' }} />
    <Heading>{card.title}</Heading><Copy>{card.body}</Copy><Text style={s.copy}>Step {page + 1} of 3</Text>
    {page === 2 && <Field label="Delivery pincode (optional)" placeholder="6-digit pincode" value={pincode} onChangeText={setPincode} keyboardType="number-pad" maxLength={6} />}
    <Button label={page === 2 ? 'Start shopping' : 'Next'} disabled={saving} onPress={() => page === 2 ? finish(true) : setPage(page + 1)} />
  </Page>;
}
