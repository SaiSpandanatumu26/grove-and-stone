import { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { api } from './api';
import { useShop } from './Store';
import { Button, Copy, Eyebrow, Field, Heading, Page, s } from './ui';

export const infoPages = ['About', 'Shipping', 'Returns', 'Contact', 'FAQ'];
export function InfoScreen({ route }: any) {
  const shop = useShop(), navigation = useNavigation<any>(), page = route.params.page;
  const [info, setInfo] = useState<any>(null), [error, setError] = useState(''), [query, setQuery] = useState(''), [opened, setOpened] = useState('');
  const [form, setForm] = useState({ full_name: shop.customer?.full_name || '', email: shop.customer?.email || '', phone: '', order_number: '', message: '' });
  const load = () => api('/shop-info').then(setInfo).catch(error => setError(error.message));
  useEffect(() => { load(); }, []);
  const faq = [
    ['When are mangoes available?', 'Check the Mangoes tab for each variety’s live season, harvest dates and waitlist. Availability can vary by variety.'],
    ['Where do you deliver?', 'Check your six-digit pincode. Coverage and fresh-fruit eligibility are checked again at checkout.'],
    ['Can I pay cash on delivery?', 'COD appears at checkout when both your selected packs and your delivery pincode allow it.'],
    ['Will my fruit be ripe?', 'Read the ripeness and handling notes on each product. Different varieties ripen at different rates.'],
    ['How should I store my order?', 'Follow the product handling notes. Keep dry fruits sealed in a cool, dry place.'],
    ['Is GST added at checkout?', 'Listed prices include GST. Your order shows the included GST separately; it is not added again. Delivery is shown before you place the order.'],
    ['Can I cancel or reorder?', 'Open Account → Orders. Confirmed orders can be cancelled before packing. Reorder adds available items to your cart at current prices.'],
  ];
  return <Page><Eyebrow>GROVE & STONE</Eyebrow><Heading>{page === 'FAQ' ? 'A little help, freshly picked.' : page === 'About' ? 'Good things, from the grove.' : page}</Heading>
    <View style={s.wrap}>{infoPages.map(item => <Button key={item} label={item} quiet={item !== page} onPress={() => navigation.setParams({ page: item })} />)}</View>
    {!!error && <View style={s.panel}><Copy>{error}</Copy><Button label="Reload support details" onPress={load} /></View>}
    <View style={[s.panel, { maxWidth: 850 }]}>
      {page === 'About' && <><Copy>Grove & Stone brings exotic fruits, dry fruits and seasonal mangoes together in one place.</Copy><Copy>Choose the pack that suits you, check delivery to your pincode, and keep your favourites close.</Copy><Copy>Browse origins, ripeness notes and seasonal availability on each product before you order.</Copy></>}
      {page === 'Shipping' && <><Copy>Delivery availability and estimated days depend on your pincode. Some areas support dry fruits only; fresh fruit orders need eligible coverage.</Copy><Copy>Choose an available delivery date within the next 14 days at checkout. We show delivery charges and your total before you place the order.</Copy>{info?.shipping_fee != null && <Copy>Delivery fee: ₹{info.shipping_fee}. Free delivery on subtotals of ₹{info.free_shipping_threshold} or more.</Copy>}<Copy>Perishable fruit needs prompt receipt and care. Use the product’s handling notes. Prices include GST, with its breakup recorded on your order.</Copy></>}
      {page === 'Returns' && <><Copy>Mangoes and exotic fruits are perishable and generally cannot be returned for a change of mind. Please contact us if there is a quality issue.</Copy><Copy>Keep your order number and clear photos of the product, packaging and label. Report quality issues {info?.quality_report_hours ? `within ${info.quality_report_hours} hours of delivery` : 'promptly after delivery'} so support can review them.</Copy><Copy>Keep dry-fruit packs sealed and retain their labels while a return request is reviewed. Support will confirm eligibility and the available resolution.</Copy><Button label="Contact us" onPress={() => navigation.setParams({ page: 'Contact' })} /></>}
      {page === 'FAQ' && <><Field label="Search questions" value={query} onChangeText={setQuery} placeholder="Delivery, mangoes, COD…" />{faq.filter(item => item.join(' ').toLowerCase().includes(query.toLowerCase())).map(([title, answer]) => <View key={title} style={{ gap: 12 }}><Button label={title} quiet onPress={() => setOpened(opened === title ? '' : title)} />{opened === title && <Copy>{answer}</Copy>}</View>)}{!faq.some(item => item.join(' ').toLowerCase().includes(query.toLowerCase())) && <Copy>No matching questions. Try another word or contact us.</Copy>}</>}
      {page === 'Contact' && <>{!!info?.support_email && <Copy>Email: {info.support_email}</Copy>}{!!info?.support_phone && <Copy>Phone: {info.support_phone}</Copy>}<Copy>Send us your question. Include your order number if it is about a purchase.</Copy>{(['full_name', 'email', 'phone', 'order_number', 'message'] as const).map(field => <Field key={field} label={({ full_name: 'Full name', email: 'Email address', phone: 'Mobile number (optional)', order_number: 'Order number (optional)', message: 'Your message' })[field]} value={form[field]} onChangeText={value => setForm({ ...form, [field]: value })} multiline={field === 'message'} maxLength={field === 'message' ? 1000 : field === 'phone' ? 10 : 320} keyboardType={field === 'email' ? 'email-address' : field === 'phone' ? 'phone-pad' : 'default'} autoCapitalize={field === 'email' ? 'none' : 'sentences'} />)}
        {info?.contact_backend === 'demo' && <Copy>Local preview: this form validates your message without sending an email.</Copy>}
        <Button label="Send message" disabled={shop.busy} onPress={() => shop.perform(async () => { const result = await api('/contact', 'POST', form); shop.setNotice(result.message); if (!result.demo) setForm({ ...form, message: '' }); })} />
      </>}
    </View>
  </Page>;
}
