import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import ChatBot from './ChatBot';
import TradingMetrics from './TradingMetrics';
import PortfolioOverview from './PortfolioOverview';
import MarketData from './MarketData';

const Dashboard: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const navigate = useNavigate();

  const navigation = [
    { name: 'Dashboard', href: '#', icon: ChartBarIcon, current: activeTab === 'dashboard' },
    { name: 'Trading', href: '/trading', icon: CurrencyDollarIcon, current: activeTab === 'trading' },
    { name: 'AI Models', href: '/ai-models', icon: ArrowTrendingUpIcon, current: activeTab === 'ai' },
    { name: 'Risk Management', href: '/risk', icon: CogIcon, current: activeTab === 'risk' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4 bg-gradient-to-r from-blue-600 to-purple-600">
            <h1 className="text-xl font-bold text-white">InfinityAI.Pro</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 ${
                  item.current
                    ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
                onClick={() => {
                  setActiveTab(item.name.toLowerCase().replace(' ', '-'));
                  setSidebarOpen(false);
                }}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            ))}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UserIcon className="w-8 h-8 text-gray-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Admin User</p>
                <p className="text-xs text-gray-500">Premium Trader</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 mt-3 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            >
              <ArrowRightOnRectangleIcon className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex items-center justify-between h-16 px-4 bg-white border-b border-gray-200 lg:px-8">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 text-gray-400 rounded-md lg:hidden hover:text-gray-500 hover:bg-gray-100"
          >
            <Bars3Icon className="w-6 h-6" />
          </button>

          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              Welcome back, <span className="font-medium text-gray-900">Admin</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500">Live Trading</span>
            </div>
          </div>
        </div>

        {/* Dashboard content */}
        <main className="p-6 lg:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
            <p className="mt-2 text-gray-600">Monitor your AI-powered trading performance and insights</p>
          </div>

          {/* Key Metrics */}
          <TradingMetrics />

          {/* Main Dashboard Grid */}
          <div className="grid grid-cols-1 gap-6 mt-8 lg:grid-cols-3">
            {/* Portfolio Overview */}
            <div className="lg:col-span-2">
              <PortfolioOverview />
            </div>

            {/* AI Chat Bot */}
            <div className="lg:col-span-1">
              <ChatBot />
            </div>
          </div>

          {/* Market Overview */}
          <div className="mt-8">
            <MarketData />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;