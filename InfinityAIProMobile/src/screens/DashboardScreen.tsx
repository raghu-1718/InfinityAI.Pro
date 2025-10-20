
import React from 'react';
import { View, StyleSheet } from 'react-native';
import MarketData from '../components/MarketData';
import TradingTerminal from '../components/TradingTerminal';

const DashboardScreen = () => {
  return (
    <View style={styles.container}>
      <MarketData />
      <TradingTerminal />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
  },
});

export default DashboardScreen;
