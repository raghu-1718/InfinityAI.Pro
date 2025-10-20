
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import io from 'socket.io-client';

const WEBSOCKET_URL = 'wss://api.infinityai.pro';

const MarketData = () => {
  const [nifty, setNifty] = useState('-');
  const [bankNifty, setBankNifty] = useState('-');

  useEffect(() => {
    const socket = io(WEBSOCKET_URL, {
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      console.log('Connected to WebSocket');
    });

    socket.on('market_data', (data) => {
      if (data.instrument === 'NIFTY') {
        setNifty(data.price);
      }
      if (data.instrument === 'BANKNIFTY') {
        setBankNifty(data.price);
      }
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
    });

    // Clean up the socket connection when the component unmounts
    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Market Data</Text>
      <Text>NIFTY: {nifty}</Text>
      <Text>BANKNIFTY: {bankNifty}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
  },
});

export default MarketData;
