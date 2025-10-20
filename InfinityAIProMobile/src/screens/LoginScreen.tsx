
import React, { useRef } from 'react';
import { View, Button } from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { WebView } from 'react-native-webview';

type LoginScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Login'>;

interface Props {
  navigation: LoginScreenNavigationProp;
}

// IMPORTANT: Replace with your actual client_id
const DHAN_OAUTH_URL = 'https://api.dhan.co/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=https://infinityai.pro/auth/dhan/callback';

const LoginScreen: React.FC<Props> = ({ navigation }) => {
  const webviewRef = useRef<WebView>(null);

  const onNavigationStateChange = (navState: any) => {
    // Check if the redirect URI is called
    if (navState.url.includes('https://infinityai.pro/auth/dhan/callback')) {
      // Extract the authorization code from the URL
      const urlParams = new URLSearchParams(navState.url.split('?')[1]);
      const authCode = urlParams.get('code');

      if (authCode) {
        // Here you would typically exchange the auth code for an access token
        // For now, we will just navigate to the dashboard
        console.log('Authorization Code:', authCode);
        navigation.replace('Dashboard');
      }
    }
  };

  return (
    <WebView
      ref={webviewRef}
      source={{ uri: DHAN_OAUTH_URL }}
      onNavigationStateChange={onNavigationStateChange}
      style={{ flex: 1 }}
    />
  );
};

export default LoginScreen;
