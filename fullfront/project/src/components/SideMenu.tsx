import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  TrendingUp,
  History,
  Brain,
  CreditCard,
  Newspaper,
  ShieldAlert,
  MessageSquare,
  Settings,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/home' },
  { icon: Briefcase, label: 'Portfolio', path: '/portfolio' },
  { icon: TrendingUp, label: 'Trade', path: '/trade' },
  { icon: History, label: 'History', path: '/history' },
  { icon: Brain, label: 'Predictor', path: '/predictor' },
  { icon: CreditCard, label: 'Subscription', path: '/subscription' },
  { icon: Newspaper, label: 'News', path: '/news' },
  { icon: ShieldAlert, label: 'Fake News Detector', path: '/fakenews' },
  { icon: MessageSquare, label: 'Chatbot', path: '/chatbot' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function SideMenu() {
  const location = useLocation();
  const { logout } = useAuth();

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
      <div className="p-6">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          PRIMEBROKER
        </h1>
        <p className="text-xs text-gray-400 mt-1">Trade Smart, Trade Secure</p>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-gray-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-red-600/10 hover:text-red-400 transition-all w-full"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}
