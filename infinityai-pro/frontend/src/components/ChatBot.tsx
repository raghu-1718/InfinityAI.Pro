import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your AI trading assistant. I can help you understand the InfinityAI.Pro platform features, trading strategies, and answer questions about your portfolio. How can I assist you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI response based on common questions
    setTimeout(() => {
      const response = generateResponse(inputMessage.toLowerCase());
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 1000 + Math.random() * 2000);
  };

  const generateResponse = (query: string): string => {
    if (query.includes('portfolio') || query.includes('balance')) {
      return 'Your portfolio shows a current value of ₹1,25,000 with a +8.2% gain today. You have 3 active positions across NIFTY and BANKNIFTY indices. Would you like me to show you detailed position information?';
    }

    if (query.includes('trading') || query.includes('strategy')) {
      return 'InfinityAI.Pro uses advanced AI algorithms combining technical analysis, sentiment analysis, and risk management. Our AI evaluates multiple factors including market trends, volatility, and historical patterns to generate trading signals with an average 68% win rate.';
    }

    if (query.includes('risk') || query.includes('management')) {
      return 'Risk management is crucial in our platform. We implement position sizing based on your capital, stop-loss orders, and maximum drawdown limits. Your current risk per trade is set to 3% of your portfolio value.';
    }

    if (query.includes('ai') || query.includes('model')) {
      return 'Our AI models are powered by Azure OpenAI GPT-4 with multi-cloud failover to AWS Bedrock. The system analyzes market data in real-time, processes news sentiment, and generates trading signals using machine learning algorithms.';
    }

    if (query.includes('dhan') || query.includes('broker')) {
      return 'We integrate with Dhan Securities for order execution. The platform supports both live and paper trading modes, with secure OAuth authentication and real-time order status updates.';
    }

    if (query.includes('performance') || query.includes('pnl')) {
      return 'Your trading performance shows consistent growth with a 68% win rate over the last 30 days. Today\'s P&L is +₹2,450, bringing your total portfolio growth to +12.5% this month.';
    }

    if (query.includes('chart') || query.includes('visual')) {
      return 'The dashboard provides real-time charts with technical indicators, candlestick patterns, and AI-generated support/resistance levels. You can view multiple timeframes from 1-minute to daily charts.';
    }

    if (query.includes('help') || query.includes('how')) {
      return 'I can help you with: 📊 Portfolio overview, 📈 Trading strategies, ⚠️ Risk management, 🤖 AI model explanations, 📉 Chart analysis, 💼 Broker integration, and 📋 Performance metrics. What would you like to know more about?';
    }

    return 'I understand you\'re asking about ' + query + '. I can provide detailed information about portfolio management, trading strategies, risk assessment, AI models, and platform features. Could you please be more specific about what you\'d like to know?';
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-colors duration-200 z-50"
        >
          <ChatBubbleLeftRightIcon className="w-6 h-6" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-lg shadow-2xl border border-gray-200 z-50 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <h3 className="font-semibold">AI Trading Assistant</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className="text-xs mt-1 opacity-70">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-3 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about trading, portfolio, or AI features..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isTyping}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white p-2 rounded-lg transition-colors duration-200"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;