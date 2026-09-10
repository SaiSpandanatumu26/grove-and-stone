import { Text, View } from 'react-native';
import { useShop } from './Store';
import { colors, Icon, IconButton, s } from './ui';

export function StockStatus() {
  const shop = useShop(), offline = shop.stockStatus === 'offline';
  return <View style={[s.between, { gap: 8 }]}><View style={[s.row, { flex: 1, gap: 8 }]}><Icon name={offline ? 'cloud-offline-outline' : 'sync-outline'} size={16} color={offline ? colors.orange : colors.green} />
    <Text accessibilityLiveRegion="polite" style={[s.copy, { fontSize: 12, flex: 1 }]}>{offline ? 'Stock check unavailable. Availability may be outdated.' : shop.stockStatus === 'paused' ? 'Stock updates paused while away.' : shop.stockCheckedAt ? 'Stock updates every 5 seconds' : 'Checking current stock…'}</Text></View>
    <IconButton label="Check stock now" icon="refresh-outline" disabled={shop.stockStatus === 'checking'} onPress={shop.refreshStock} />
  </View>;
}
