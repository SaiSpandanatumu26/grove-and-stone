import { ActivityIndicator, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { AccountScreen } from './src/Account';
import { CartScreen, PincodeScreen } from './src/Cart';
import { CheckoutScreen, OrderScreen } from './src/Checkout';
import { InfoScreen } from './src/Info';
import { HomeScreen, MangoScreen, ProductScreen, SearchScreen, WaitlistScreen } from './src/Home';
import { ShopProvider, useShop } from './src/Store';
import { Button, colors, Icon, IconButton, IconName, s, useWide } from './src/ui';

type Tabs = { Home: undefined; Mangoes: undefined; Cart: undefined; Account: undefined };
type Stack = { Landing: { section?: string; next?: string } | undefined; Product: { slug: string }; Waitlist: { slug: string }; Search: undefined; Pincode: undefined; Checkout: undefined; Order: { number: string }; Info: { page: string } };
const Tab = createBottomTabNavigator<Tabs>(), Screen = createNativeStackNavigator<Stack>();
const pages = { Home: HomeScreen, Mangoes: MangoScreen, Cart: CartScreen, Account: AccountScreen };
const icons: Record<keyof Tabs, IconName> = { Home: 'home-outline', Mangoes: 'leaf-outline', Cart: 'bag-handle-outline', Account: 'person-outline' };
const theme = { ...DefaultTheme, colors: { ...DefaultTheme.colors, primary: colors.orange, background: '#FFFFFF', card: '#FFFFFF', text: colors.dark, border: colors.line } };

function TabStack({ route, navigation: tabNav }: any) {
  const shop = useShop(), wide = useWide(), name = route.name as keyof Tabs;
  return <Screen.Navigator screenOptions={({ navigation }) => ({
    headerShadowVisible: false, headerTintColor: colors.orange, contentStyle: { backgroundColor: '#FFFFFF' },
    headerTitle: () => <View style={s.row}><Icon name={icons[name]} size={24} />{wide && <Text style={{ color: colors.orange, fontWeight: '900', fontSize: 23, letterSpacing: -0.7 }}>grove<Text style={{ color: '#ECA613' }}>&stone</Text></Text>}</View>,
    headerRight: () => <View style={[s.row, { gap: wide ? 10 : 0 }]}>
      <Button label={shop.cart?.pincode || 'Deliver to'} quiet icon="location-outline" onPress={() => navigation.navigate('Pincode')} />
      <IconButton label="Search products" icon="search-outline" onPress={() => navigation.navigate('Search')} />
      {wide && <Button label={shop.customer ? shop.customer.full_name.split(' ')[0] : 'Login'} quiet icon="person-outline" onPress={() => tabNav.navigate('Account')} />}
    </View>,
  })}>
    <Screen.Screen name="Landing" component={pages[name]} options={{ title: 'Grove & Stone' }} />
    <Screen.Screen name="Product" component={ProductScreen} />
    <Screen.Screen name="Waitlist" component={WaitlistScreen} />
    <Screen.Screen name="Search" component={SearchScreen} />
    <Screen.Screen name="Pincode" component={PincodeScreen} />
    <Screen.Screen name="Checkout" component={CheckoutScreen} />
    <Screen.Screen name="Order" component={OrderScreen} />
    <Screen.Screen name="Info" component={InfoScreen} />
  </Screen.Navigator>;
}

function Storefront() {
  const shop = useShop(), count = shop.cart?.lines.reduce((sum, line) => sum + line.qty, 0) || 0;
  return <View style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
    {!!shop.notice && <View accessibilityLiveRegion="polite" style={[s.between, { paddingHorizontal: 18, backgroundColor: '#FFF0D8', minHeight: 50 }]}><Text style={{ color: '#77440B', flex: 1, fontSize: 14 }}>{shop.notice}</Text><IconButton label="Dismiss message" icon="close" onPress={() => shop.setNotice('')} /></View>}
    {!shop.ready ? <View style={s.empty}><ActivityIndicator color={colors.orange} /><Text style={s.copy}>Getting the grove ready... The first visit may take about a minute.</Text></View> : shop.failed ? <View style={s.empty}><Text style={s.copy}>The shop could not load.</Text><Button label="Try again" onPress={shop.reload} disabled={shop.busy} /></View> :
      <NavigationContainer theme={theme}><Tab.Navigator initialRouteName="Home" backBehavior="history" screenOptions={({ route }) => ({
        headerShown: false, tabBarActiveTintColor: colors.orange, tabBarInactiveTintColor: '#8A847C', tabBarStyle: { borderTopColor: colors.line, minHeight: 66 }, tabBarItemStyle: { minHeight: 56 }, tabBarLabelStyle: { fontSize: 12, fontWeight: '700' },
        tabBarIcon: ({ color }) => <Icon name={icons[route.name]} color={color} size={22} />,
        tabBarBadge: route.name === 'Cart' && count ? count : undefined, tabBarBadgeStyle: { backgroundColor: colors.orange, color: '#FFFFFF' },
      })}>{(Object.keys(pages) as (keyof Tabs)[]).map(name => <Tab.Screen key={name} name={name} component={TabStack} />)}</Tab.Navigator></NavigationContainer>}
  </View>;
}
export default function App() { return <SafeAreaProvider><StatusBar style="dark" /><ShopProvider><Storefront /></ShopProvider></SafeAreaProvider>; }
