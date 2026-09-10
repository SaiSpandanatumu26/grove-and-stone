import { ReactNode } from 'react';
import { Image, ImageStyle, Pressable, ScrollView, StyleProp, StyleSheet, Text, TextInput, TextInputProps, View, useWindowDimensions } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { media } from './api';

export const colors = { orange: '#EC650E', dark: '#292624', muted: '#706B63', yellow: '#FFBE21', cream: '#FFFAF2', line: '#F0E8DD', green: '#407B38' };
export type IconName = React.ComponentProps<typeof Ionicons>['name'];
export const money = (value: string | number = 0) => '₹' + Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const dateLabel = (value: string) => new Date(value.length === 10 ? value + 'T12:00:00' : value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
export const useWide = () => useWindowDimensions().width >= 820;
export const Icon = ({ name, size = 22, color = colors.orange }: { name: IconName; size?: number; color?: string }) => <Ionicons name={name} size={size} color={color} />;
export const Heading = ({ children }: { children: ReactNode }) => <Text accessibilityRole="header" style={s.heading}>{children}</Text>;
export const Copy = ({ children }: { children: ReactNode }) => <Text style={s.copy}>{children}</Text>;
export const Eyebrow = ({ children }: { children: ReactNode }) => <Text style={s.eyebrow}>{children}</Text>;
export function Button({ label, onPress, icon, quiet = false, disabled = false }: { label: string; onPress: () => void; icon?: IconName; quiet?: boolean; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [s.button, quiet && s.quiet, { opacity: disabled ? 0.45 : pressed ? 0.7 : 1 }]}>
    {icon && <Icon name={icon} size={19} color={quiet ? colors.orange : '#FFFFFF'} />}<Text style={[s.buttonText, quiet && { color: colors.orange }]}>{label}</Text>
  </Pressable>;
}
export function IconButton({ label, icon, onPress, active = false, disabled = false }: { label: string; icon: IconName; onPress: () => void; active?: boolean; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} accessibilityState={{ disabled, selected: active }} onPress={onPress}
    style={[s.iconButton, active && { backgroundColor: '#FFF0D9' }, disabled && { opacity: 0.4 }]}><Icon name={icon} color={active ? colors.orange : colors.dark} /></Pressable>;
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  return <View style={{ gap: 7, flexGrow: 1 }}><Text style={s.label}>{label}</Text><TextInput accessibilityLabel={label} placeholderTextColor="#8B857B" {...props} style={[s.input, props.style]} /></View>;
}
export const Photo = ({ src, label, style }: { src: string; label: string; style?: StyleProp<ImageStyle> }) => <Image source={{ uri: media(src) }} accessibilityLabel={label} resizeMode="cover" style={[s.photo, style]} />;
export function Page({ children }: { children: ReactNode }) { return <ScrollView style={s.page} contentContainerStyle={s.pageContent} keyboardShouldPersistTaps="handled"><View style={s.container}>{children}</View></ScrollView>; }
export function Empty({ icon, title, body, children }: { icon: IconName; title: string; body: string; children?: ReactNode }) {
  return <View style={s.empty}><View style={s.emptyIcon}><Icon name={icon} size={42} /></View><Heading>{title}</Heading><Copy>{body}</Copy>{children}</View>;
}
export const s = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#FFFFFF' }, pageContent: { padding: 24, paddingBottom: 60 }, container: { maxWidth: 1180, width: '100%', alignSelf: 'center', gap: 24 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12 }, wrap: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12 }, between: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 16 },
  heading: { fontSize: 29, fontWeight: '800', letterSpacing: -0.8, color: colors.dark }, copy: { color: colors.muted, fontSize: 15, lineHeight: 24 }, eyebrow: { color: colors.orange, fontWeight: '800', letterSpacing: 2, fontSize: 11, textTransform: 'uppercase' },
  button: { minHeight: 48, paddingVertical: 12, paddingHorizontal: 21, backgroundColor: colors.orange, borderRadius: 9, flexDirection: 'row', gap: 9, justifyContent: 'center', alignItems: 'center' },
  quiet: { backgroundColor: '#FFF1DE' }, buttonText: { color: '#FFFFFF', fontSize: 14, fontWeight: '700' }, iconButton: { width: 48, height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  input: { borderWidth: 1, borderColor: '#DED7CC', backgroundColor: '#FAF9F7', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 12, minHeight: 48, color: colors.dark, fontSize: 15 }, label: { fontSize: 13, fontWeight: '700', color: colors.dark },
  photo: { width: '100%', aspectRatio: 1, backgroundColor: colors.cream, borderRadius: 14 }, panel: { padding: 26, borderWidth: 1, borderColor: colors.line, borderRadius: 16, backgroundColor: '#FFFFFF', gap: 20 },
  empty: { alignItems: 'center', paddingVertical: 52, paddingHorizontal: 16, gap: 20 }, emptyIcon: { padding: 23, backgroundColor: '#FFF2DD', borderRadius: 50 },
  badge: { backgroundColor: '#ECF4E9', color: colors.green, paddingVertical: 6, paddingHorizontal: 10, borderRadius: 6, fontSize: 12, fontWeight: '700', alignSelf: 'flex-start' }, divider: { height: 1, backgroundColor: colors.line },
});
