
import React, { useState } from 'react';
import { View, TextInput, Button, StyleSheet, Alert } from 'react-native';

const CHATBOT_API_URL = 'https://engine.infinityai.pro/execute_trade';

const TradingTerminal = () => {
  const [command, setCommand] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleExecute = async () => {
    if (!command.trim()) {
      Alert.alert('Error', 'Please enter a trade command.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(CHATBOT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      });

      const result = await response.json();

      if (response.ok) {
        Alert.alert('Success', `Trade executed: ${result.message}`);
        setCommand('');
      } else {
        Alert.alert('Error', `Failed to execute trade: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error executing trade:', error);
      Alert.alert('Error', 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Enter your trade command (e.g., BUY 100 RELIANCE)"
        value={command}
        onChangeText={setCommand}
        editable={!isLoading}
      />
      <Button title={isLoading ? 'Executing...' : 'Execute'} onPress={handleExecute} disabled={isLoading} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 5,
  },
  input: {
    height: 40,
    borderColor: 'gray',
    borderWidth: 1,
    marginBottom: 10,
    paddingHorizontal: 10,
  },
});

export default TradingTerminal;
